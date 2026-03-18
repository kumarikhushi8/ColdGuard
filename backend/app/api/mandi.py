from fastapi import APIRouter, Depends, Query
from typing import Optional
import asyncpg
from app.core.database import get_db
from app.services.advisory_engine import get_facility_advisory
from app.services.mandi_service import MANDI_CROP_MAP, simulate_price, save_prices

router = APIRouter()


@router.get("/prices")
async def get_prices(
    crop:   Optional[str] = None,
    market: Optional[str] = None,
    limit:  int = 50,
    conn: asyncpg.Connection = Depends(get_db),
):
    """Latest mandi prices, optionally filtered by crop or market."""
    filters = []
    params  = []

    if crop:
        params.append(crop.lower())
        filters.append(f"LOWER(mp.crop) = ${len(params)}")
    if market:
        params.append(f"%{market}%")
        filters.append(f"mp.market ILIKE ${len(params)}")

    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    params.append(limit)

    rows = await conn.fetch(f"""
        SELECT DISTINCT ON (mp.crop, mp.market)
            mp.time, mp.crop, mp.market,
            mp.price_min, mp.price_max, mp.price_modal, mp.unit
        FROM mandi_prices mp
        {where}
        ORDER BY mp.crop, mp.market, mp.time DESC
        LIMIT ${len(params)}
    """, *params)

    return [dict(r) for r in rows]


@router.get("/prices/summary")
async def price_summary(conn: asyncpg.Connection = Depends(get_db)):
    """Price summary per crop with 7-day trend."""
    rows = await conn.fetch("""
        WITH latest AS (
            SELECT DISTINCT ON (crop)
                crop, price_modal as current_price, time
            FROM mandi_prices
            ORDER BY crop, time DESC
        ),
        week_ago AS (
            SELECT DISTINCT ON (crop)
                crop, price_modal as old_price
            FROM mandi_prices
            WHERE time < NOW() - INTERVAL '6 days'
            ORDER BY crop, time DESC
        )
        SELECT
            l.crop,
            l.current_price,
            w.old_price,
            CASE
                WHEN w.old_price IS NULL THEN 'stable'
                WHEN l.current_price > w.old_price * 1.03 THEN 'rising'
                WHEN l.current_price < w.old_price * 0.97 THEN 'falling'
                ELSE 'stable'
            END as trend,
            ROUND(
                CASE WHEN w.old_price > 0
                THEN ((l.current_price - w.old_price) / w.old_price * 100)
                ELSE 0 END, 1
            ) as change_pct
        FROM latest l
        LEFT JOIN week_ago w ON w.crop = l.crop
        ORDER BY l.crop
    """)
    return [dict(r) for r in rows]


@router.get("/prices/history/{crop}")
async def price_history(
    crop: str,
    days: int = 30,
    conn: asyncpg.Connection = Depends(get_db),
):
    """Price history for a crop over time (for charts)."""
    rows = await conn.fetch("""
        SELECT
            date_trunc('day', time) AS day,
            crop,
            AVG(price_modal) AS avg_modal,
            MIN(price_min)   AS min_price,
            MAX(price_max)   AS max_price,
            COUNT(*)         AS market_count
        FROM mandi_prices
        WHERE LOWER(crop) = LOWER($1)
          AND time > NOW() - ($2 || ' days')::INTERVAL
        GROUP BY day, crop
        ORDER BY day ASC
    """, crop, str(days))
    return [dict(r) for r in rows]


@router.get("/advisory/{facility_id}")
async def facility_advisory(
    facility_id: str,
    conn: asyncpg.Connection = Depends(get_db),
):
    """Generate sell/hold/move advisory for a specific facility."""
    advisory = await get_facility_advisory(conn, facility_id)
    if not advisory:
        return {"error": "Facility not found"}

    return {
        "action":        advisory.action,
        "urgency":       advisory.urgency,
        "reason":        advisory.reason,
        "crop":          advisory.crop,
        "price_trend":   advisory.price_trend,
        "current_price": advisory.current_price,
        "price_7d_ago":  advisory.price_7d_ago,
        "risk_score":    advisory.risk_score,
        "explanation":   {
            "en": advisory.explanation_en,
            "hi": advisory.explanation_hi,
            "mr": advisory.explanation_mr,
        },
    }


@router.get("/advisory/all/summary")
async def all_advisories(conn: asyncpg.Connection = Depends(get_db)):
    """Advisory summary for all facilities."""
    facilities = await conn.fetch("SELECT id, name, location FROM facilities ORDER BY name")
    result = []
    for f in facilities:
        advisory = await get_facility_advisory(conn, str(f["id"]))
        if advisory:
            result.append({
                "facility_id":   str(f["id"]),
                "facility_name": f["name"],
                "action":        advisory.action,
                "urgency":       advisory.urgency,
                "crop":          advisory.crop,
                "current_price": advisory.current_price,
                "price_trend":   advisory.price_trend,
                "risk_score":    advisory.risk_score,
                "explanation_en": advisory.explanation_en,
                "explanation_mr": advisory.explanation_mr,
            })
    return result


@router.post("/prices/seed-demo")
async def seed_demo_prices(conn: asyncpg.Connection = Depends(get_db)):
    """Seed realistic demo prices for all tracked mandis. Useful on first run."""
    from app.services.mandi_service import PRICE_PROFILES
    count = 0
    for market, crops in MANDI_CROP_MAP.items():
        for crop in crops:
            # Seed 7 days of history
            for day_offset in range(7, -1, -1):
                price = simulate_price(crop.lower(), market, day_offset)
                await conn.execute("""
                    INSERT INTO mandi_prices (time, crop, market, price_min, price_max, price_modal)
                    VALUES (NOW() - ($1 || ' days')::INTERVAL, $2, $3, $4, $5, $6)
                """, str(day_offset), price["crop"], price["market"],
                    price["price_min"], price["price_max"], price["price_modal"])
                count += 1
    return {"seeded": count, "message": "Demo prices loaded for all mandis"}
