"""
Sensor Simulator — National Coverage
Generates realistic readings for all facilities across all states.
Temperature profiles vary by state climate.
"""

import asyncio
import asyncpg
import random
import math
import logging
import json
from datetime import datetime, timezone
from app.core.config import get_settings
from app.ml.risk_engine import compute_risk, SensorReading

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Base temp by state (reflects ambient climate difficulty)
STATE_BASE_TEMP = {
    "Maharashtra": 4.0,  "Punjab": 3.0,     "Uttar Pradesh": 4.5,
    "Karnataka": 5.0,    "Gujarat": 5.5,    "Himachal Pradesh": 1.5,
    "Rajasthan": 6.0,    "West Bengal": 5.0, "Tamil Nadu": 6.0,
    "Bihar": 5.0,
}

SENSOR_STATES: dict[str, dict] = {}

def get_state_from_location(location: str) -> str:
    for state in STATE_BASE_TEMP:
        if state.lower() in location.lower():
            return state
    return "Maharashtra"

def init_sensor_state(sensor_id: str, location: str) -> dict:
    state    = get_state_from_location(location)
    base_tmp = STATE_BASE_TEMP.get(state, 4.0)
    return {
        "base_temp":          base_tmp + random.uniform(-0.5, 0.5),
        "base_rh":            random.uniform(78.0, 90.0),
        "drift":              0.0,
        "excursion_minutes":  0,
        "failure_mode":       None,
        "tick":               0,
        "location":           location,
    }

def next_reading(sensor_id: str, location: str) -> dict:
    state = SENSOR_STATES.setdefault(sensor_id, init_sensor_state(sensor_id, location))
    state["tick"] += 1
    t = state["tick"]

    # Trigger failure ~2% of ticks
    if random.random() < 0.02 and state["failure_mode"] is None:
        state["failure_mode"] = random.choice(["gradual_warm", "sudden_spike", "humidity_drop"])

    # Clear failure after 30 ticks
    if state["failure_mode"] and t % 30 == 0:
        state["failure_mode"] = None
        state["drift"] = 0.0

    if state["failure_mode"] == "gradual_warm":
        state["drift"] += 0.3
    elif state["failure_mode"] == "sudden_spike":
        state["drift"] = random.uniform(8, 14)
    elif state["failure_mode"] is None:
        state["drift"] = max(0.0, state["drift"] - 0.1)

    diurnal     = math.sin(t / 60 * math.pi) * 0.5
    temperature = state["base_temp"] + state["drift"] + diurnal + random.gauss(0, 0.15)
    humidity    = max(0, min(100, state["base_rh"] + random.gauss(0, 0.5) - (15 if state["failure_mode"] == "humidity_drop" else 0)))
    eth_base    = 0.05 + max(0, (temperature - 8) * 0.3)
    ethylene    = max(0, eth_base + random.gauss(0, 0.02))

    if temperature > state["base_temp"] + 2:
        state["excursion_minutes"] += 1
    else:
        state["excursion_minutes"] = max(0, state["excursion_minutes"] - 1)

    return {
        "temperature":        round(temperature, 2),
        "humidity":           round(humidity, 2),
        "ethylene_ppm":       round(ethylene, 4),
        "battery_pct":        round(max(10, 100 - t * 0.005 + random.gauss(0, 0.3)), 1),
        "rssi":               random.randint(-85, -45),
        "excursion_minutes":  state["excursion_minutes"],
    }


async def run_simulator():
    settings = get_settings()
    logger.info("Simulator starting — waiting 8s for DB...")
    await asyncio.sleep(8)

    pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)

    async with pool.acquire() as conn:
        sensors = await conn.fetch("""
            SELECT s.id, s.sensor_code, s.facility_id, f.location
            FROM sensors s
            JOIN facilities f ON f.id = s.facility_id
            WHERE s.active = TRUE
        """)

    logger.info(f"Simulating {len(sensors)} sensors across all facilities")

    while True:
        async with pool.acquire() as conn:
            for sensor in sensors:
                sid      = str(sensor["id"])
                location = sensor["location"] or ""
                reading  = next_reading(sid, str(sensor["facility_id"]))

                await conn.execute("""
                    INSERT INTO sensor_readings
                        (time, sensor_id, temperature, humidity, ethylene_ppm, battery_pct, rssi)
                    VALUES (NOW(), $1, $2, $3, $4, $5, $6)
                """, sensor["id"], reading["temperature"], reading["humidity"],
                    reading["ethylene_ppm"], reading["battery_pct"], reading["rssi"])

                risk = compute_risk(SensorReading(
                    temperature=reading["temperature"],
                    humidity=reading["humidity"],
                    ethylene_ppm=reading["ethylene_ppm"],
                    excursion_minutes=reading["excursion_minutes"],
                ))

                await conn.execute("""
                    INSERT INTO risk_scores (time, facility_id, risk_score, risk_level, contributing_factors)
                    VALUES (NOW(), $1, $2, $3, $4)
                """, sensor["facility_id"], risk.score, risk.level, json.dumps(risk.factors))

                if risk.level in ("high", "critical"):
                    logger.info(f"[{sensor['sensor_code']}] T={reading['temperature']:.1f}°C RISK={risk.level.upper()}({risk.score:.2f})")

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_simulator())
