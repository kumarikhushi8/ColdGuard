"""
Advisory Engine — National Coverage
Sell/hold/move decisions for all 10 states.
"""

import asyncpg
import logging
from dataclasses import dataclass
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ─── Crop profiles per city ───────────────────────────────────────────────────
LOCATION_CROP_MAP = {
    # Maharashtra
    "nashik": "grapes",       "pune": "tomato",         "solapur": "pomegranate",
    "kolhapur": "tomato",     "mumbai": "tomato",
    # Punjab
    "amritsar": "apple",      "ludhiana": "potato",     "jalandhar": "potato",
    "patiala": "potato",      "bhatinda": "onion",
    # Uttar Pradesh
    "agra": "potato",         "lucknow": "mango",       "prayagraj": "guava",
    "varanasi": "tomato",     "mathura": "potato",
    # Karnataka
    "hubli": "grapes",        "bangalore": "tomato",    "belagavi": "pomegranate",
    "shivamogga": "banana",   "mysore": "tomato",
    # Gujarat
    "surat": "banana",        "rajkot": "potato",       "junagadh": "mango",
    "anand": "potato",        "bhavnagar": "banana",
    # Himachal Pradesh
    "shimla": "apple",        "manali": "apple",        "kullu": "apple",
    "mandi": "pear",          "solan": "cherry",
    # Rajasthan
    "jaipur": "onion",        "jodhpur": "garlic",      "alwar": "chilli",
    "kota": "onion",          "bikaner": "onion",
    # West Bengal
    "kolkata": "potato",      "siliguri": "mango",      "murshidabad": "lychee",
    "hooghly": "potato",      "burdwan": "potato",
    # Tamil Nadu
    "coimbatore": "banana",   "salem": "tomato",        "madurai": "mango",
    "tiruchirappalli": "banana", "erode": "banana",
    # Bihar
    "patna": "mango",         "muzaffarpur": "lychee",  "gaya": "potato",
    "bhagalpur": "mango",     "darbhanga": "potato",
    # Default
    "default": "onion",
}

def guess_crop(location: str) -> str:
    loc = location.lower()
    for city, crop in LOCATION_CROP_MAP.items():
        if city in loc:
            return crop
    return LOCATION_CROP_MAP["default"]


@dataclass
class Advisory:
    action: str
    urgency: str
    reason: str
    price_trend: str
    current_price: Optional[float]
    price_7d_ago: Optional[float]
    risk_score: float
    crop: str
    explanation_en: str
    explanation_hi: str
    explanation_mr: str


async def get_price_trend(conn: asyncpg.Connection, crop: str, location: str) -> dict:
    city = location.split(",")[0].strip()

    row = await conn.fetchrow("""
        WITH latest AS (
            SELECT price_modal, time
            FROM mandi_prices
            WHERE LOWER(crop) = LOWER($1)
              AND (LOWER(market) LIKE LOWER($2) OR market = $3)
            ORDER BY time DESC LIMIT 1
        ),
        week_ago AS (
            SELECT price_modal
            FROM mandi_prices
            WHERE LOWER(crop) = LOWER($1)
              AND (LOWER(market) LIKE LOWER($2) OR market = $3)
              AND time < NOW() - INTERVAL '6 days'
            ORDER BY time DESC LIMIT 1
        )
        SELECT l.price_modal as current_price, w.price_modal as old_price
        FROM latest l LEFT JOIN week_ago w ON TRUE
    """, crop, f"%{city}%", city)

    if not row or not row["current_price"]:
        # Fallback to any market for this crop
        row = await conn.fetchrow("""
            WITH latest AS (
                SELECT price_modal FROM mandi_prices
                WHERE LOWER(crop) = LOWER($1)
                ORDER BY time DESC LIMIT 1
            ),
            week_ago AS (
                SELECT price_modal FROM mandi_prices
                WHERE LOWER(crop) = LOWER($1) AND time < NOW() - INTERVAL '6 days'
                ORDER BY time DESC LIMIT 1
            )
            SELECT l.price_modal as current_price, w.price_modal as old_price
            FROM latest l LEFT JOIN week_ago w ON TRUE
        """, crop)

    if not row or not row["current_price"]:
        return {"current_price": None, "price_7d_ago": None, "trend": "unknown"}

    current = float(row["current_price"])
    old     = float(row["old_price"]) if row.get("old_price") else None
    trend   = "stable"
    if current and old:
        pct = (current - old) / old * 100
        trend = "rising" if pct > 3 else "falling" if pct < -3 else "stable"

    return {"current_price": current, "price_7d_ago": old, "trend": trend}


def compute_advisory(risk_score: float, risk_level: str, price_data: dict) -> tuple[str, str]:
    trend = price_data["trend"]
    if risk_level == "critical":
        return ("MOVE_CROP", "critical") if trend == "falling" else ("SELL_NOW", "critical")
    if risk_level == "high":
        return "SELL_NOW", "high"
    if risk_level == "medium":
        return ("SELL_SOON", "medium") if trend == "rising" else ("SELL_SOON", "high")
    return ("HOLD", "low") if trend in ("rising", "stable") else ("SELL_SOON", "medium")


async def generate_explanation(action, crop, facility_name, risk_score, price_data, urgency) -> dict:
    price_str = f"₹{price_data['current_price']:.0f}/quintal" if price_data["current_price"] else "price unavailable"
    trend_str = price_data["trend"]

    fallbacks = {
        "SELL_NOW":  f"Sell your {crop} immediately. Risk is {risk_score:.0%} and current price is {price_str}.",
        "SELL_SOON": f"Plan to sell your {crop} within 2-3 days. Risk is rising ({risk_score:.0%}). Price trend: {trend_str}.",
        "HOLD":      f"Hold your {crop} — conditions stable. Price is {trend_str} at {price_str}. Risk low ({risk_score:.0%}).",
        "MOVE_CROP": f"Move your {crop} to better storage urgently. Risk critical ({risk_score:.0%}) and price is falling.",
    }
    msg = fallbacks.get(action, f"Monitor your {crop} storage closely.")

    try:
        from deep_translator import GoogleTranslator
        hi_translator = GoogleTranslator(source='en', target='hi')
        mr_translator = GoogleTranslator(source='en', target='mr')
        return {
            "en": msg,
            "hi": hi_translator.translate(msg),
            "mr": mr_translator.translate(msg)
        }
    except Exception as e:
        logger.debug(f"Advisory explanation translation failed: {e}")

    return {"en": msg, "hi": msg, "mr": msg}


async def get_facility_advisory(conn: asyncpg.Connection, facility_id: str) -> Optional[Advisory]:
    facility = await conn.fetchrow("SELECT name, location FROM facilities WHERE id = $1", facility_id)
    if not facility:
        return None

    risk_row = await conn.fetchrow("""
        SELECT risk_score, risk_level FROM risk_scores
        WHERE facility_id = $1 ORDER BY time DESC LIMIT 1
    """, facility_id)

    risk_score = float(risk_row["risk_score"]) if risk_row else 0.05
    risk_level = risk_row["risk_level"] if risk_row else "low"
    crop       = guess_crop(facility["location"])
    price_data = await get_price_trend(conn, crop, facility["location"])
    action, urgency = compute_advisory(risk_score, risk_level, price_data)

    explanations = await generate_explanation(
        action, crop, facility["name"], risk_score, price_data, urgency
    )

    reason_map = {
        "SELL_NOW":  "High spoilage risk — sell before losses compound.",
        "SELL_SOON": "Moderate risk or declining prices — plan sale within 3 days.",
        "HOLD":      "Low risk and stable/rising prices — safe to wait.",
        "MOVE_CROP": "Critical risk with poor prices — relocate to better storage.",
    }

    return Advisory(
        action=action, urgency=urgency, reason=reason_map[action],
        price_trend=price_data["trend"],
        current_price=price_data["current_price"],
        price_7d_ago=price_data["price_7d_ago"],
        risk_score=risk_score, crop=crop,
        explanation_en=explanations.get("en", ""),
        explanation_hi=explanations.get("hi", ""),
        explanation_mr=explanations.get("mr", ""),
    )
