from fastapi import APIRouter, Depends, Query
from typing import Optional
import asyncpg
from app.core.database import get_db

router = APIRouter()

@router.get("/summary")
async def get_summary(
    state: Optional[str] = Query(None, description="Filter by state name"),
    conn: asyncpg.Connection = Depends(get_db),
):
    filters = ["1=1"]
    params  = []
    if state:
        params.append(f"%{state}%")
        filters.append(f"f.location ILIKE ${len(params)}")

    where = " AND ".join(filters)

    facilities = await conn.fetch(f"""
        SELECT f.id, f.name, f.location, f.owner_name,
               f.capacity_mt,
               rs.risk_score, rs.risk_level,
               sr.temperature, sr.humidity, sr.ethylene_ppm,
               sr.time as last_reading
        FROM facilities f
        LEFT JOIN LATERAL (
            SELECT risk_score, risk_level FROM risk_scores
            WHERE facility_id = f.id ORDER BY time DESC LIMIT 1
        ) rs ON TRUE
        LEFT JOIN LATERAL (
            SELECT sr.temperature, sr.humidity, sr.ethylene_ppm, sr.time
            FROM sensor_readings sr
            JOIN sensors s ON s.id = sr.sensor_id
            WHERE s.facility_id = f.id ORDER BY sr.time DESC LIMIT 1
        ) sr ON TRUE
        WHERE {where}
        ORDER BY COALESCE(rs.risk_score, 0) DESC
    """, *params)

    unacked_alerts = await conn.fetch("""
        SELECT a.id, a.facility_id, f.name as facility_name,
               a.alert_type, a.severity, a.message,
               a.message_hi, a.message_mr, a.created_at
        FROM alerts a
        JOIN facilities f ON f.id = a.facility_id
        WHERE a.acknowledged = FALSE
        ORDER BY a.created_at DESC LIMIT 20
    """)

    total    = len(facilities)
    critical = sum(1 for f in facilities if f["risk_level"] == "critical")
    high     = sum(1 for f in facilities if f["risk_level"] == "high")

    # State breakdown for filter dropdown
    all_states = await conn.fetch("""
        SELECT DISTINCT
            TRIM(SPLIT_PART(location, ',', 2)) as state,
            COUNT(*) as facility_count
        FROM facilities
        WHERE location LIKE '%,%'
        GROUP BY state
        ORDER BY state
    """)

    return {
        "stats": {
            "total_facilities": total,
            "critical_count":   critical,
            "high_risk_count":  high,
            "healthy_count":    total - critical - high,
            "unacked_alerts":   len(unacked_alerts),
        },
        "facilities":   [dict(f) for f in facilities],
        "alerts":       [dict(a) for a in unacked_alerts],
        "states":       [dict(s) for s in all_states],
    }


@router.get("/facility/{facility_id}/trend")
async def get_trend(facility_id: str, hours: int = 24, conn: asyncpg.Connection = Depends(get_db)):
    rows = await conn.fetch("""
        SELECT
            date_trunc('hour', sr.time) AS bucket,
            AVG(sr.temperature)  AS avg_temp,
            AVG(sr.humidity)     AS avg_rh,
            AVG(sr.ethylene_ppm) AS avg_eth,
            MAX(rs.risk_score)   AS max_risk
        FROM sensor_readings sr
        JOIN sensors s ON s.id = sr.sensor_id
        LEFT JOIN risk_scores rs
            ON rs.facility_id = s.facility_id
            AND rs.time BETWEEN sr.time - INTERVAL '15 minutes'
                            AND sr.time + INTERVAL '15 minutes'
        WHERE s.facility_id = $1
          AND sr.time > NOW() - ($2 || ' hours')::INTERVAL
        GROUP BY bucket ORDER BY bucket ASC
    """, facility_id, str(hours))
    return [dict(r) for r in rows]


@router.get("/states")
async def list_states(conn: asyncpg.Connection = Depends(get_db)):
    """All states with facility counts."""
    rows = await conn.fetch("""
        SELECT
            TRIM(SPLIT_PART(location, ',', 2)) as state,
            COUNT(*) as facility_count,
            SUM(capacity_mt) as total_capacity_mt
        FROM facilities
        WHERE location LIKE '%,%'
        GROUP BY state ORDER BY state
    """)
    return [dict(r) for r in rows]
