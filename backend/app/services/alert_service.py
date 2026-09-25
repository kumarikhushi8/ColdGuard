"""
Alert Service
Creates alert records, translates them, and dispatches WhatsApp/SMS.
"""

import anthropic
import asyncpg
import logging
from app.core.config import get_settings
from app.ml.risk_engine import RiskResult

logger = logging.getLogger(__name__)


async def translate_alert(message: str) -> dict[str, str]:
    """Use Claude to translate alert into Hindi and Marathi."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        return {"hi": message, "mr": message}

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"""Translate this cold storage alert for Indian farmers.
Return ONLY a JSON object with keys "hi" (Hindi) and "mr" (Marathi).
Use simple, clear language a rural farmer would understand.
Alert: {message}"""
            }]
        )
        import json, re
        text = resp.content[0].text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        logger.warning(f"Translation failed: {e}")

    return {"hi": message, "mr": message}


async def create_alert(
    conn: asyncpg.Connection,
    facility_id: str,
    sensor_id: str | None,
    alert_type: str,
    severity: str,
    message: str,
) -> dict:
    """Create an alert record with translations, then dispatch notifications."""
    translations = await translate_alert(message)

    row = await conn.fetchrow("""
        INSERT INTO alerts (facility_id, sensor_id, alert_type, severity, message, message_hi, message_mr)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """, facility_id, sensor_id, alert_type, severity, message,
        translations.get("hi", message), translations.get("mr", message))

    alert = dict(row)

    # Fetch facility owner contact and dispatch notification
    try:
        facility = await conn.fetchrow(
            "SELECT name, owner_phone FROM facilities WHERE id = $1",
            facility_id
        )
        if facility:
            from app.services.notification_service import dispatch_alert
            await dispatch_alert(
                facility_id=str(facility_id),
                facility_name=facility["name"],
                owner_phone=facility["owner_phone"],
                severity=severity,
                message_en=message,
                message_hi=translations.get("hi", message),
                message_mr=translations.get("mr", message),
            )
    except Exception as e:
        logger.error(f"Notification dispatch failed: {e}")

    return alert


async def check_and_alert(
    conn: asyncpg.Connection,
    facility_id: str,
    sensor_id: str,
    temperature: float,
    humidity: float,
    ethylene_ppm: float,
    risk: RiskResult,
) -> list[dict]:
    settings = get_settings()
    alerts = []

    # Temperature alerts
    if temperature > settings.temp_critical:
        alerts.append(await create_alert(
            conn, facility_id, sensor_id, "temperature_critical", "critical",
            f"CRITICAL: Temperature {temperature:.1f}C — far above safe range. Immediate action required."
        ))
    elif temperature > settings.temp_warning:
        alerts.append(await create_alert(
            conn, facility_id, sensor_id, "temperature_warning", "warning",
            f"WARNING: Temperature {temperature:.1f}C — above safe threshold. Check cooling system."
        ))

    # Ethylene alerts
    if ethylene_ppm > settings.ethylene_critical:
        alerts.append(await create_alert(
            conn, facility_id, sensor_id, "ethylene_critical", "critical",
            f"CRITICAL: Ethylene {ethylene_ppm:.2f} ppm — high ripening gas. Risk of rapid spoilage."
        ))

    # Risk-level alerts
    if risk.level == "critical":
        alerts.append(await create_alert(
            conn, facility_id, sensor_id, "spoilage_risk", "critical",
            f"Spoilage risk CRITICAL ({risk.score:.0%}). {risk.recommendation}"
        ))
    elif risk.level == "high":
        alerts.append(await create_alert(
            conn, facility_id, sensor_id, "spoilage_risk", "warning",
            f"Spoilage risk HIGH ({risk.score:.0%}). {risk.recommendation}"
        ))

    return alerts
