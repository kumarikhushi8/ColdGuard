"""
Spoilage Risk Engine
Computes a 0-1 risk score from sensor readings using a rule-based model
backed by research from ICAR post-harvest loss studies.

Risk factors (weighted):
  - Temperature deviation from optimal (40%)
  - Duration of temperature excursion (25%)
  - Relative humidity (20%)
  - Ethylene concentration (15%)
"""

from dataclasses import dataclass
from typing import Optional
import math

CROP_PROFILES = {
    "tomato":    {"opt_temp": 12.0, "opt_rh": 90, "eth_sensitivity": "high"},
    "onion":     {"opt_temp": 1.0,  "opt_rh": 70, "eth_sensitivity": "low"},
    "potato":    {"opt_temp": 4.0,  "opt_rh": 95, "eth_sensitivity": "low"},
    "mango":     {"opt_temp": 13.0, "opt_rh": 85, "eth_sensitivity": "high"},
    "grapes":    {"opt_temp": 0.0,  "opt_rh": 90, "eth_sensitivity": "medium"},
    "default":   {"opt_temp": 4.0,  "opt_rh": 85, "eth_sensitivity": "medium"},
}

@dataclass
class SensorReading:
    temperature: float
    humidity: float
    ethylene_ppm: float
    excursion_minutes: int = 0  # minutes outside safe range

@dataclass
class RiskResult:
    score: float          # 0.0 – 1.0
    level: str            # low / medium / high / critical
    factors: dict
    recommendation: str

def compute_risk(reading: SensorReading, crop: str = "default") -> RiskResult:
    profile = CROP_PROFILES.get(crop, CROP_PROFILES["default"])
    factors = {}

    # 1. Temperature deviation score (0-1)
    temp_dev = abs(reading.temperature - profile["opt_temp"])
    temp_score = min(1.0, temp_dev / 15.0)
    factors["temperature_deviation"] = round(temp_dev, 2)
    factors["temperature_score"] = round(temp_score, 3)

    # 2. Duration penalty — risk compounds with time above threshold
    duration_score = 0.0
    if temp_dev > 2.0:
        duration_score = min(1.0, reading.excursion_minutes / 240.0)  # 4h = max
    factors["excursion_minutes"] = reading.excursion_minutes
    factors["duration_score"] = round(duration_score, 3)

    # 3. Humidity score
    rh_dev = abs(reading.humidity - profile["opt_rh"])
    rh_score = min(1.0, rh_dev / 30.0)
    factors["humidity_score"] = round(rh_score, 3)

    # 4. Ethylene score
    eth_multiplier = {"high": 1.5, "medium": 1.0, "low": 0.5}[profile["eth_sensitivity"]]
    eth_score = min(1.0, (reading.ethylene_ppm * eth_multiplier) / 5.0)
    factors["ethylene_score"] = round(eth_score, 3)

    # Weighted combination
    raw = (
        temp_score    * 0.40 +
        duration_score * 0.25 +
        rh_score      * 0.20 +
        eth_score     * 0.15
    )

    # Sigmoid smoothing
    score = 1 / (1 + math.exp(-10 * (raw - 0.5)))
    score = round(min(0.99, max(0.01, score)), 4)

    # Level thresholds
    if score < 0.30:
        level = "low"
        recommendation = "Conditions optimal. No action needed."
    elif score < 0.55:
        level = "medium"
        recommendation = "Monitor closely. Check temperature calibration."
    elif score < 0.75:
        level = "high"
        recommendation = "Inspect facility. Consider early market dispatch."
    else:
        level = "critical"
        recommendation = "URGENT: Immediate inspection required. Alert farmer now."

    return RiskResult(score=score, level=level, factors=factors, recommendation=recommendation)
