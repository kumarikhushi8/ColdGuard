"""
Analytics API
Business metrics: loss prevented, ROI, excursions, reports.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import asyncpg
import json
import io
import csv
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import require_operator
from app.services.analytics_engine import (
    compute_facility_analytics,
    compute_system_analytics,
    BASELINE_LOSS_PCT, MONITORED_LOSS_PCT, LOSS_PREVENTED_PCT,
    CROP_VALUE_PER_MT, SUBSCRIPTION_COST_PER_MT_MONTH,
)

router = APIRouter()


@router.get("/summary")
async def analytics_summary(
    days: int = Query(30, ge=7, le=365),
    conn: asyncpg.Connection = Depends(get_db),
    user: dict = Depends(require_operator),
):
    """Full system analytics summary — the numbers that win grants."""
    data = await compute_system_analytics(conn, days)
    return {
        "period_days":              data.period_days,
        "total_facilities":         data.total_facilities,
        "total_sensors":            data.total_sensors,
        "total_readings":           data.total_readings,
        "total_loss_prevented_mt":  data.total_loss_prevented_mt,
        "total_loss_prevented_inr": data.total_loss_prevented_inr,
        "total_subscription_cost":  data.total_subscription_cost,
        "system_roi_pct":           data.system_roi_pct,
        "total_excursions":         data.total_excursions,
        "total_alerts":             data.total_alerts,
        "avg_risk_score":           data.avg_risk_score,
        "facilities": [
            {
                "facility_id":        f.facility_id,
                "facility_name":      f.facility_name,
                "location":           f.location,
                "capacity_mt":        f.capacity_mt,
                "crop":               f.crop,
                "loss_prevented_mt":  f.loss_prevented_mt,
                "loss_prevented_inr": f.loss_prevented_inr,
                "roi_pct":            f.roi_pct,
                "payback_days":       f.payback_days,
                "excursion_count":    f.excursion_count,
                "critical_excursions": f.critical_excursions,
                "uptime_pct":         f.uptime_pct,
                "alerts_total":       f.alerts_total,
                "alerts_critical":    f.alerts_critical,
                "avg_ack_minutes":    f.avg_ack_minutes,
                "subscription_cost":  f.subscription_cost,
            }
            for f in data.facilities
        ],
    }


@router.get("/facility/{facility_id}")
async def facility_analytics(
    facility_id: str,
    days: int = Query(30, ge=7, le=365),
    conn: asyncpg.Connection = Depends(get_db),
    user: dict = Depends(require_operator),
):
    """Detailed analytics for one facility."""
    data = await compute_facility_analytics(conn, facility_id, days)
    if not data:
        return {"error": "Facility not found"}
    return data.__dict__


@router.get("/risk-timeline")
async def risk_timeline(
    days: int = Query(7, ge=1, le=90),
    conn: asyncpg.Connection = Depends(get_db),
    user: dict = Depends(require_operator),
):
    """Daily avg risk score per facility for timeline chart."""
    rows = await conn.fetch("""
        SELECT
            DATE_TRUNC('day', rs.time) as day,
            f.name as facility_name,
            AVG(rs.risk_score) as avg_risk,
            MAX(rs.risk_score) as max_risk,
            COUNT(*) FILTER (WHERE rs.risk_level IN ('high','critical')) as high_count
        FROM risk_scores rs
        JOIN facilities f ON f.id = rs.facility_id
        WHERE rs.time > NOW() - ($1 || ' days')::INTERVAL
        GROUP BY day, f.name
        ORDER BY day ASC, f.name
    """, str(days))
    return [dict(r) for r in rows]


@router.get("/excursions")
async def excursion_log(
    days: int = Query(30, ge=1, le=365),
    facility_id: str = None,
    conn: asyncpg.Connection = Depends(get_db),
    user: dict = Depends(require_operator),
):
    """Temperature excursion events log."""
    filters = ["sr.temperature > 8", f"sr.time > NOW() - ('{days} days')::INTERVAL"]
    params  = []

    if facility_id:
        params.append(facility_id)
        filters.append(f"s.facility_id = ${len(params)}")

    rows = await conn.fetch(f"""
        SELECT
            DATE_TRUNC('hour', sr.time) as hour,
            f.name as facility_name,
            s.sensor_code,
            AVG(sr.temperature) as avg_temp,
            MAX(sr.temperature) as max_temp,
            COUNT(*) as reading_count,
            CASE
                WHEN MAX(sr.temperature) > 15 THEN 'critical'
                WHEN MAX(sr.temperature) > 10 THEN 'major'
                ELSE 'minor'
            END as severity
        FROM sensor_readings sr
        JOIN sensors s ON s.id = sr.sensor_id
        JOIN facilities f ON f.id = s.facility_id
        WHERE {' AND '.join(filters)}
        GROUP BY hour, f.name, s.sensor_code
        ORDER BY hour DESC
        LIMIT 200
    """, *params)
    return [dict(r) for r in rows]


@router.get("/roi-model")
async def roi_model(
    capacity_mt: float = Query(500, description="Storage capacity in MT"),
    crop: str = Query("tomato", description="Primary crop stored"),
    days: int = Query(30, ge=1),
    sensors: int = Query(3, description="Number of sensor nodes"),
):
    """
    Interactive ROI calculator — no DB needed.
    Used for sales pitches and grant applications.
    """
    crop_value = CROP_VALUE_PER_MT.get(crop.lower(), CROP_VALUE_PER_MT["default"])
    baseline_loss_inr  = capacity_mt * BASELINE_LOSS_PCT * crop_value * (days / 30)
    monitored_loss_inr = capacity_mt * MONITORED_LOSS_PCT * crop_value * (days / 30)
    loss_prevented_inr = baseline_loss_inr - monitored_loss_inr
    loss_prevented_mt  = capacity_mt * LOSS_PREVENTED_PCT * (days / 30)

    subscription_cost = capacity_mt * SUBSCRIPTION_COST_PER_MT_MONTH * (days / 30)
    hardware_cost     = sensors * 2500

    net_benefit    = loss_prevented_inr - subscription_cost
    roi_pct        = (net_benefit / max(subscription_cost, 1)) * 100
    payback_days   = hardware_cost / max(loss_prevented_inr / days, 1)

    return {
        "inputs": {
            "capacity_mt":  capacity_mt,
            "crop":         crop,
            "crop_value_per_mt": crop_value,
            "period_days":  days,
            "sensors":      sensors,
        },
        "loss_model": {
            "baseline_loss_pct":    f"{BASELINE_LOSS_PCT:.0%}",
            "monitored_loss_pct":   f"{MONITORED_LOSS_PCT:.0%}",
            "loss_prevented_pct":   f"{LOSS_PREVENTED_PCT:.0%}",
            "baseline_loss_mt":     round(capacity_mt * BASELINE_LOSS_PCT * (days/30), 2),
            "monitored_loss_mt":    round(capacity_mt * MONITORED_LOSS_PCT * (days/30), 2),
            "loss_prevented_mt":    round(loss_prevented_mt, 2),
            "baseline_loss_inr":    round(baseline_loss_inr, 0),
            "monitored_loss_inr":   round(monitored_loss_inr, 0),
            "loss_prevented_inr":   round(loss_prevented_inr, 0),
        },
        "roi": {
            "subscription_cost_inr": round(subscription_cost, 0),
            "hardware_cost_inr":     hardware_cost,
            "net_benefit_inr":       round(net_benefit, 0),
            "roi_pct":               round(roi_pct, 1),
            "payback_days":          round(payback_days, 0),
        },
        "source": "ICAR Post-Harvest Loss Study 2022",
    }


@router.get("/report/csv")
async def download_csv(
    days: int = Query(30),
    conn: asyncpg.Connection = Depends(get_db),
    user: dict = Depends(require_operator),
):
    """Download analytics report as CSV — for sharing with investors/FPOs."""
    data = await compute_system_analytics(conn, days)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["ColdGuard Analytics Report"])
    writer.writerow([f"Period: Last {days} days", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
    writer.writerow([])

    # System summary
    writer.writerow(["SYSTEM SUMMARY"])
    writer.writerow(["Total Facilities",       data.total_facilities])
    writer.writerow(["Total Sensors",          data.total_sensors])
    writer.writerow(["Total Readings",         data.total_readings])
    writer.writerow(["Loss Prevented (MT)",    data.total_loss_prevented_mt])
    writer.writerow(["Loss Prevented (₹)",     f"₹{data.total_loss_prevented_inr:,.0f}"])
    writer.writerow(["System ROI",             f"{data.system_roi_pct:.1f}%"])
    writer.writerow(["Total Excursions",       data.total_excursions])
    writer.writerow(["Total Alerts",           data.total_alerts])
    writer.writerow([])

    # Per-facility
    writer.writerow([
        "Facility", "Location", "Crop", "Capacity (MT)",
        "Loss Prevented (MT)", "Loss Prevented (₹)",
        "ROI %", "Payback (days)",
        "Excursions", "Critical", "Uptime %",
        "Alerts", "Subscription Cost (₹)"
    ])
    for f in data.facilities:
        writer.writerow([
            f.facility_name, f.location, f.crop, f.capacity_mt,
            f.loss_prevented_mt, f.loss_prevented_inr,
            f.roi_pct, f.payback_days,
            f.excursion_count, f.critical_excursions, f.uptime_pct,
            f.alerts_total, f.subscription_cost,
        ])

    output.seek(0)
    filename = f"coldguard_report_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
