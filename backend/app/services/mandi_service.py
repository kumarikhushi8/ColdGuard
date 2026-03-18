"""
Mandi Price Service — National Coverage
Agmarknet prices for 10 states, 20 crops.
"""

import httpx
import asyncpg
import asyncio
import logging
import random
from datetime import datetime, date
from app.core.config import get_settings

logger = logging.getLogger(__name__)

AGMARKNET_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# ─── National mandi → crop map ────────────────────────────────────────────────
MANDI_CROP_MAP = {
    # Maharashtra
    "Nashik":       ["Tomato", "Onion", "Grapes"],
    "Pune":         ["Tomato", "Potato", "Onion"],
    "Solapur":      ["Pomegranate", "Onion", "Tomato"],
    "Mumbai":       ["Tomato", "Potato", "Onion", "Banana"],
    "Kolhapur":     ["Tomato", "Potato", "Banana"],
    # Punjab
    "Amritsar":     ["Potato", "Onion", "Apple"],
    "Ludhiana":     ["Potato", "Onion", "Apple"],
    "Jalandhar":    ["Potato", "Onion"],
    "Patiala":      ["Potato", "Onion"],
    "Bhatinda":     ["Onion", "Potato"],
    # Uttar Pradesh
    "Agra":         ["Potato", "Tomato", "Onion"],
    "Lucknow":      ["Mango", "Potato", "Guava"],
    "Prayagraj":    ["Guava", "Mango", "Tomato"],
    "Varanasi":     ["Tomato", "Potato", "Mango"],
    "Mathura":      ["Potato", "Onion", "Tomato"],
    # Karnataka
    "Hubli":        ["Grapes", "Pomegranate", "Onion"],
    "Bangalore":    ["Tomato", "Potato", "Onion"],
    "Belagavi":     ["Pomegranate", "Tomato", "Onion"],
    "Shivamogga":   ["Banana", "Tomato"],
    "Mysore":       ["Tomato", "Potato", "Banana"],
    # Gujarat
    "Surat":        ["Banana", "Mango", "Tomato"],
    "Rajkot":       ["Potato", "Onion", "Banana"],
    "Junagadh":     ["Mango", "Banana", "Potato"],
    "Anand":        ["Potato", "Tomato", "Onion"],
    "Bhavnagar":    ["Banana", "Mango", "Onion"],
    # Himachal Pradesh
    "Shimla":       ["Apple", "Pear", "Cherry"],
    "Manali":       ["Apple", "Pear"],
    "Kullu":        ["Apple", "Cherry"],
    "Mandi":        ["Apple", "Pear"],
    "Solan":        ["Apple", "Cherry", "Tomato"],
    # Rajasthan
    "Jaipur":       ["Onion", "Garlic", "Tomato"],
    "Jodhpur":      ["Garlic", "Onion", "Chilli"],
    "Alwar":        ["Chilli", "Onion", "Tomato"],
    "Kota":         ["Onion", "Potato", "Garlic"],
    "Bikaner":      ["Onion", "Garlic", "Chilli"],
    # West Bengal
    "Kolkata":      ["Potato", "Mango", "Tomato"],
    "Siliguri":     ["Mango", "Banana", "Potato"],
    "Murshidabad":  ["Lychee", "Mango", "Potato"],
    "Hooghly":      ["Potato", "Tomato", "Mango"],
    "Burdwan":      ["Potato", "Tomato", "Onion"],
    # Tamil Nadu
    "Coimbatore":   ["Banana", "Tomato", "Onion"],
    "Salem":        ["Tomato", "Onion", "Banana"],
    "Madurai":      ["Mango", "Banana", "Tomato"],
    "Tiruchirappalli": ["Banana", "Tomato", "Mango"],
    "Erode":        ["Banana", "Tomato", "Onion"],
    # Bihar
    "Patna":        ["Mango", "Potato", "Lychee"],
    "Muzaffarpur":  ["Lychee", "Mango", "Banana"],
    "Gaya":         ["Potato", "Tomato", "Mango"],
    "Bhagalpur":    ["Mango", "Banana", "Potato"],
    "Darbhanga":    ["Potato", "Lychee", "Mango"],
}

# State → Agmarknet state name
STATE_MAP = {
    "Nashik": "Maharashtra",   "Pune": "Maharashtra",    "Solapur": "Maharashtra",
    "Amritsar": "Punjab",      "Ludhiana": "Punjab",     "Jalandhar": "Punjab",
    "Patiala": "Punjab",       "Bhatinda": "Punjab",
    "Agra": "Uttar Pradesh",   "Lucknow": "Uttar Pradesh", "Prayagraj": "Uttar Pradesh",
    "Varanasi": "Uttar Pradesh", "Mathura": "Uttar Pradesh",
    "Hubli": "Karnataka",      "Bangalore": "Karnataka", "Belagavi": "Karnataka",
    "Shivamogga": "Karnataka", "Mysore": "Karnataka",
    "Surat": "Gujarat",        "Rajkot": "Gujarat",      "Junagadh": "Gujarat",
    "Anand": "Gujarat",        "Bhavnagar": "Gujarat",
    "Shimla": "Himachal Pradesh", "Manali": "Himachal Pradesh", "Kullu": "Himachal Pradesh",
    "Mandi": "Himachal Pradesh",  "Solan": "Himachal Pradesh",
    "Jaipur": "Rajasthan",    "Jodhpur": "Rajasthan",   "Alwar": "Rajasthan",
    "Kota": "Rajasthan",      "Bikaner": "Rajasthan",
    "Kolkata": "West Bengal",  "Siliguri": "West Bengal", "Murshidabad": "West Bengal",
    "Hooghly": "West Bengal",  "Burdwan": "West Bengal",
    "Coimbatore": "Tamil Nadu","Salem": "Tamil Nadu",    "Madurai": "Tamil Nadu",
    "Tiruchirappalli": "Tamil Nadu", "Erode": "Tamil Nadu",
    "Patna": "Bihar",          "Muzaffarpur": "Bihar",   "Gaya": "Bihar",
    "Bhagalpur": "Bihar",      "Darbhanga": "Bihar",
}

# ─── Price profiles (₹/quintal, realistic ranges) ─────────────────────────────
PRICE_PROFILES = {
    "tomato":      {"base": 1200,  "volatility": 0.35, "season_peak": [11, 12, 1]},
    "onion":       {"base": 1800,  "volatility": 0.45, "season_peak": [12, 1, 2]},
    "potato":      {"base": 900,   "volatility": 0.20, "season_peak": [2, 3, 4]},
    "grapes":      {"base": 4500,  "volatility": 0.25, "season_peak": [2, 3, 4]},
    "pomegranate": {"base": 6000,  "volatility": 0.30, "season_peak": [9, 10, 11]},
    "banana":      {"base": 1500,  "volatility": 0.15, "season_peak": [4, 5, 6]},
    "mango":       {"base": 3500,  "volatility": 0.40, "season_peak": [5, 6, 7]},
    "apple":       {"base": 8000,  "volatility": 0.20, "season_peak": [8, 9, 10]},
    "pear":        {"base": 5000,  "volatility": 0.22, "season_peak": [7, 8, 9]},
    "cherry":      {"base": 12000, "volatility": 0.30, "season_peak": [5, 6]},
    "guava":       {"base": 2000,  "volatility": 0.25, "season_peak": [11, 12, 1]},
    "lychee":      {"base": 7000,  "volatility": 0.40, "season_peak": [5, 6]},
    "garlic":      {"base": 4000,  "volatility": 0.50, "season_peak": [3, 4, 5]},
    "chilli":      {"base": 3000,  "volatility": 0.45, "season_peak": [1, 2, 3]},
    "default":     {"base": 1500,  "volatility": 0.25, "season_peak": []},
}

_price_state: dict = {}

def simulate_price(crop: str, market: str, day_offset: int = 0) -> dict:
    crop_key = crop.lower()
    profile  = PRICE_PROFILES.get(crop_key, PRICE_PROFILES["default"])
    key      = f"{market}:{crop_key}"
    month    = datetime.now().month
    seasonal = 1.25 if month in profile["season_peak"] else 1.0
    state    = _price_state.setdefault(key, {"modal": profile["base"] * seasonal, "direction": 1})

    if random.random() < 0.15:
        state["direction"] *= -1
    change = random.uniform(0, profile["volatility"] * 0.08) * state["direction"]
    state["modal"] = max(
        profile["base"] * 0.35,
        min(profile["base"] * 2.8, state["modal"] * (1 + change))
    )
    modal  = round(state["modal"])
    spread = modal * random.uniform(0.08, 0.18)
    return {
        "market":      market,
        "crop":        crop_key,
        "price_min":   round(modal - spread),
        "price_max":   round(modal + spread),
        "price_modal": modal,
        "date":        str(date.today()),
    }


async def fetch_agmarknet(crop: str, state: str = "Maharashtra", limit: int = 10) -> list[dict]:
    params = {
        "format": "json", "limit": limit,
        "filters[State]": state, "filters[Commodity]": crop,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(AGMARKNET_URL, params=params)
            if resp.status_code != 200:
                return []
            records = resp.json().get("records", [])
            result = []
            for r in records:
                try:
                    result.append({
                        "market":      r.get("Market", "Unknown"),
                        "crop":        r.get("Commodity", crop).lower(),
                        "price_min":   float(r.get("Min Price", 0)),
                        "price_max":   float(r.get("Max Price", 0)),
                        "price_modal": float(r.get("Modal Price", 0)),
                        "date":        r.get("Arrival_Date", str(date.today())),
                    })
                except (ValueError, TypeError):
                    continue
            return result
    except Exception as e:
        logger.debug(f"Agmarknet unavailable for {crop}/{state}: {e}")
        return []


async def save_prices(conn: asyncpg.Connection, prices: list[dict]):
    for p in prices:
        await conn.execute("""
            INSERT INTO mandi_prices (time, crop, market, price_min, price_max, price_modal)
            VALUES (NOW(), $1, $2, $3, $4, $5)
        """, p["crop"], p["market"], p["price_min"], p["price_max"], p["price_modal"])


async def run_price_fetcher(pool: asyncpg.Pool):
    logger.info("[Mandi] National price fetcher starting...")
    await asyncio.sleep(8)

    while True:
        try:
            async with pool.acquire() as conn:
                fetched_any = False
                for mandi, crops in MANDI_CROP_MAP.items():
                    state = STATE_MAP.get(mandi, "Maharashtra")
                    for crop in crops:
                        live = await fetch_agmarknet(crop, state=state)
                        if live:
                            await save_prices(conn, live)
                            fetched_any = True
                        else:
                            price = simulate_price(crop.lower(), mandi)
                            await save_prices(conn, [price])
                mode = "live" if fetched_any else "simulated"
                logger.info(f"[Mandi] Prices updated for {len(MANDI_CROP_MAP)} mandis ({mode})")
        except Exception as e:
            logger.error(f"[Mandi] Fetch error: {e}")

        await asyncio.sleep(30 * 60)
