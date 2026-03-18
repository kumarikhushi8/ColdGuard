"""
Analytics Engine
Computes business metrics from sensor + risk + mandi price data.

Key metrics:
  - Spoilage loss prevented (kg + ₹) vs baseline without monitoring
  - Temperature excursion events: count, duration, severity
  - ROI: subscription cost vs loss prevented
  - Facility uptime / SLA
  - Alert response time

Research basis:
  ICAR (2022): Average post-harvest loss in India = 15-18% without monitoring
  ColdGuard target: reduce to 3-5% through early warning
  Default assumption: 13% loss prevented per MT stored
"""

import asyncpg
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Constants (ICAR-based) ────────────────────────────────────────────────────

BASELINE_LOSS_PCT    = 0.16   # 16% loss without monitoring (ICAR average)
MONITORED_LOSS_PCT   = 0.04   # 4% loss with ColdGuard active
LOSS_PREVENTED_PCT   = BASELINE_LOSS_PCT - MONITORED_LOSS_PCT  # 12%

SUBSCRIPTION_COST_PER_MT_MONTH = 5.0   # ₹5/MT/month (target pricing)
SENSOR_NODE_COST     = 2500.0   # ₹2500 per sensor node (hardware)

# Average crop values ₹/MT (conservative, based on Agmarknet 2023-24)
CROP_VALUE_PER_MT = {
    "tomato":      8000,
    "onion":      12000,
    "potato":      6000,
    "grapes":     35000,
    "pomegranate": 45000,
    "banana":     10000,
    "mango":      25000,
    "default":    10000,
}


@dataclass
class ExcursionEvent:
    facility_id:   str
    facility_name: str
    started_at:    datetime
    ended_at:      Optional[datetime]
    max_temp:      float
    duration_mins: int
    severity:      str   # minor | major | critical


@dataclass
class FacilityAnalytics:
    facility_id:      str
    facility_name:    str
    location:         str
    capacity_mt:      float
    crop:             str
    period_days:      int

    # Excursions
    excursion_count:  int
    total_excursion_mins: int
    critical_excursions: int

    # Loss model
    baseline_loss_mt:   float     # MT lost without monitoring
    monitored_loss_mt:  float     # MT lost with monitoring
    loss_prevented_mt:  float     # MT saved
    crop_value_per_mt:  float     # ₹/MT
    loss_prevented_inr: float     # ₹ value saved

    # ROI
    subscription_cost:  float     # ₹ for the period
    roi_pct:            float     # (saved - cost) / cost × 100
    payback_days:       float     # days to recover sensor cost

    # Uptime
    readings_count:     int
    uptime_pct:         float     # % of expected readings received

    # Alerts
    alerts_total:       int
    alerts_critical:    int
    alerts_acked:       int
    avg_ack_minutes:    Optional[float]


@dataclass
class SystemAnalytics:
    period_days:         int
    total_facilities:    int
    total_sensors:       int
    total_readings:      int

    total_loss_prevented_mt:  float
    total_loss_prevented_inr: float
    total_subscription_cost:  float
    system_roi_pct:           float

    total_excursions:    int
    total_alerts:        int
    avg_risk_score:      float

    facilities:          list[FacilityAnalytics] = field(default_factory=list)


# ─── Core computation ──────────────────────────────────────────────────────────

async def compute_facility_analytics(
    conn: asyncpg.Connection,
    facility_id: str,
    period_days: int = 30,
) -> Optional[FacilityAnalytics]:

    facility = await conn.fetchrow(
        "SELECT id, name, location, capacity_mt FROM facilities WHERE id = $1", facility_id
    )
    if not facility:
        return None

    capacity_mt = float(facility["capacity_mt"] or 100)
    location    = facility["location"]

    # Guess crop from location
    from app.services.advisory_engine import guess_crop
    crop = guess_crop(location)
    crop_value = CROP_VALUE_PER_MT.get(crop, CROP_VALUE_PER_MT["default"])

    # ── Readings & uptime ────────────────────────────────────────────────────
    readings = await conn.fetchrow("""
        SELECT COUNT(*) as cnt,
               AVG(sr.temperature) as avg_temp,
               MAX(sr.temperature) as max_temp,
               MIN(sr.temperature) as min_temp
        FROM sensor_readings sr
        JOIN sensors s ON s.id = sr.sensor_id
        WHERE s.facility_id = $1
          AND sr.time > NOW() - ($2 || ' days')::INTERVAL
    """, facility_id, str(period_days))

    readings_count = int(readings["cnt"] or 0)
    # Expected: 1 reading per sensor per 10 min → 6/hr × 24hr × days × sensors
    sensor_count = await conn.fetchval(
        "SELECT COUNT(*) FROM sensors WHERE facility_id = $1 AND active = TRUE", facility_id
    )
    expected = int(sensor_count or 1) * period_days * 24 * 6
    uptime_pct = min(100.0, (readings_count / max(expected, 1)) * 100)

    # ── Excursion events ──────────────────────────────────────────────────────
    # Count readings where temp > threshold as proxy for excursion minutes
    excursion_data = await conn.fetchrow("""
        SELECT
            COUNT(*) FILTER (WHERE sr.temperature > 8)  as excursion_readings,
            COUNT(*) FILTER (WHERE sr.temperature > 12) as critical_readings,
            COUNT(DISTINCT DATE_TRUNC('hour', sr.time))
                FILTER (WHERE sr.temperature > 8)       as excursion_hours
        FROM sensor_readings sr
        JOIN sensors s ON s.id = sr.sensor_id
        WHERE s.facility_id = $1
          AND sr.time > NOW() - ($2 || ' days')::INTERVAL
    """, facility_id, str(period_days))

    excursion_mins    = int(excursion_data["excursion_readings"] or 0) * 10
    critical_readings = int(excursion_data["critical_readings"] or 0)
    excursion_hours   = int(excursion_data["excursion_hours"] or 0)
    excursion_count   = max(1, excursion_hours // 4) if excursion_hours > 0 else 0
    critical_events   = max(0, critical_readings // 6)

    # ── Risk scores ───────────────────────────────────────────────────────────
    risk_data = await conn.fetchrow("""
        SELECT AVG(risk_score) as avg_risk, MAX(risk_score) as max_risk
        FROM risk_scores
        WHERE facility_id = $1
          AND time > NOW() - ($2 || ' days')::INTERVAL
    """, facility_id, str(period_days))

    avg_risk = float(risk_data["avg_risk"] or 0.05)

    # ── Alerts ────────────────────────────────────────────────────────────────
    alert_data = await conn.fetchrow("""
        SELECT
            COUNT(*)                           as total,
            COUNT(*) FILTER (WHERE severity = 'critical') as critical_cnt,
            COUNT(*) FILTER (WHERE acknowledged = TRUE)   as acked,
            AVG(EXTRACT(EPOCH FROM (ack_at - created_at)) / 60)
                FILTER (WHERE acknowledged = TRUE)        as avg_ack_mins
        FROM alerts
        WHERE facility_id = $1
          AND created_at > NOW() - ($2 || ' days')::INTERVAL
    """, facility_id, str(period_days))

    # ── Loss model ────────────────────────────────────────────────────────────
    # Adjust loss prevented by actual risk level observed
    risk_multiplier   = 1.0 + (avg_risk - 0.05) * 2   # more risk = more saved
    loss_prevented_mt = capacity_mt * LOSS_PREVENTED_PCT * risk_multiplier * (period_days / 30)
    loss_prevented_mt = min(loss_prevented_mt, capacity_mt * 0.20)   # cap at 20%

    baseline_loss_mt  = capacity_mt * BASELINE_LOSS_PCT * (period_days / 30)
    monitored_loss_mt = baseline_loss_mt - loss_prevented_mt
    loss_prevented_inr = loss_prevented_mt * crop_value

    # ── ROI ───────────────────────────────────────────────────────────────────
    subscription_cost = capacity_mt * SUBSCRIPTION_COST_PER_MT_MONTH * (period_days / 30)
    net_saved   = loss_prevented_inr - subscription_cost
    roi_pct     = (net_saved / max(subscription_cost, 1)) * 100

    total_sensor_cost = int(sensor_count or 1) * SENSOR_NODE_COST
    payback_days = (total_sensor_cost / max(loss_prevented_inr / period_days, 1))

    return FacilityAnalytics(
        facility_id=str(facility["id"]),
        facility_name=facility["name"],
        location=location,
        capacity_mt=capacity_mt,
        crop=crop,
        period_days=period_days,
        excursion_count=excursion_count,
        total_excursion_mins=excursion_mins,
        critical_excursions=critical_events,
        baseline_loss_mt=round(baseline_loss_mt, 2),
        monitored_loss_mt=round(monitored_loss_mt, 2),
        loss_prevented_mt=round(loss_prevented_mt, 2),
        crop_value_per_mt=crop_value,
        loss_prevented_inr=round(loss_prevented_inr, 0),
        subscription_cost=round(subscription_cost, 0),
        roi_pct=round(roi_pct, 1),
        payback_days=round(payback_days, 0),
        readings_count=readings_count,
        uptime_pct=round(uptime_pct, 1),
        alerts_total=int(alert_data["total"] or 0),
        alerts_critical=int(alert_data["critical_cnt"] or 0),
        alerts_acked=int(alert_data["acked"] or 0),
        avg_ack_minutes=round(float(alert_data["avg_ack_mins"]), 1) if alert_data["avg_ack_mins"] else None,
    )


async def compute_system_analytics(
    conn: asyncpg.Connection,
    period_days: int = 30,
) -> SystemAnalytics:
    facilities = await conn.fetch("SELECT id FROM facilities")

    analytics_list = []
    for f in facilities:
        fa = await compute_facility_analytics(conn, str(f["id"]), period_days)
        if fa:
            analytics_list.append(fa)

    total_sensors = await conn.fetchval(
        "SELECT COUNT(*) FROM sensors WHERE active = TRUE"
    )
    total_readings = await conn.fetchval("""
        SELECT COUNT(*) FROM sensor_readings
        WHERE time > NOW() - ($1 || ' days')::INTERVAL
    """, str(period_days))
    avg_risk = await conn.fetchval("""
        SELECT AVG(risk_score) FROM risk_scores
        WHERE time > NOW() - ($1 || ' days')::INTERVAL
    """, str(period_days))
    total_alerts = await conn.fetchval("""
        SELECT COUNT(*) FROM alerts
        WHERE created_at > NOW() - ($1 || ' days')::INTERVAL
    """, str(period_days))

    total_saved_mt  = sum(a.loss_prevented_mt  for a in analytics_list)
    total_saved_inr = sum(a.loss_prevented_inr for a in analytics_list)
    total_cost      = sum(a.subscription_cost  for a in analytics_list)
    total_exc       = sum(a.excursion_count    for a in analytics_list)
    system_roi      = ((total_saved_inr - total_cost) / max(total_cost, 1)) * 100

    return SystemAnalytics(
        period_days=period_days,
        total_facilities=len(analytics_list),
        total_sensors=int(total_sensors or 0),
        total_readings=int(total_readings or 0),
        total_loss_prevented_mt=round(total_saved_mt, 2),
        total_loss_prevented_inr=round(total_saved_inr, 0),
        total_subscription_cost=round(total_cost, 0),
        system_roi_pct=round(system_roi, 1),
        total_excursions=total_exc,
        total_alerts=int(total_alerts or 0),
        avg_risk_score=round(float(avg_risk or 0.05), 4),
        facilities=analytics_list,
    )
