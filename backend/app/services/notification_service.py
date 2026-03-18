"""
Notification Service
Sends alerts via:
  1. WhatsApp Business API (Meta Cloud API) — primary channel
  2. SMS via fast2sms.com — fallback / simultaneous

Setup guide is printed to logs on first run.
"""

import httpx
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ─── cooldown tracker (in-memory, resets on container restart) ───────────────
_last_notified: dict[str, float] = {}  # facility_id -> unix timestamp


def _is_on_cooldown(facility_id: str) -> bool:
    import time
    settings = get_settings()
    last = _last_notified.get(facility_id, 0)
    cooldown_secs = settings.alert_cooldown_minutes * 60
    return (time.time() - last) < cooldown_secs


def _mark_notified(facility_id: str):
    import time
    _last_notified[facility_id] = time.time()


# ─── WhatsApp Business API ────────────────────────────────────────────────────

async def send_whatsapp(
    phone: str,
    message: str,
    language: str = "en",
    facility_name: str = "",
    severity: str = "warning",
) -> bool:
    """
    Send a WhatsApp message via Meta Cloud API.

    Uses a text message (not template) for sandbox/testing.
    For production you need an approved template.

    phone format: "919876543210" (country code + number, no +)
    """
    settings = get_settings()

    if not settings.whatsapp_enabled:
        logger.info(f"[WhatsApp MOCK] → {phone}: {message[:80]}...")
        return True

    if not settings.whatsapp_token or not settings.whatsapp_phone_id:
        logger.warning("WhatsApp not configured. Set WHATSAPP_TOKEN and WHATSAPP_PHONE_ID.")
        return False

    phone = phone.replace("+", "").replace("-", "").replace(" ", "")
    if not phone.startswith("91"):
        phone = "91" + phone

    url = f"https://graph.facebook.com/v19.0/{settings.whatsapp_phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }

    # Use free-form text for test numbers; use template for production
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                logger.info(f"[WhatsApp] Sent to {phone[-4:]}**** ✓")
                return True
            else:
                logger.error(f"[WhatsApp] Failed {resp.status_code}: {resp.text[:200]}")
                return False
    except Exception as e:
        logger.error(f"[WhatsApp] Exception: {e}")
        return False


# ─── SMS via fast2sms.com ─────────────────────────────────────────────────────

async def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS via fast2sms.com (Indian provider, free tier available).
    Sign up at https://www.fast2sms.com — get API key from dashboard.

    phone: "9876543210" (10-digit Indian mobile, no country code)
    """
    settings = get_settings()

    if not settings.sms_enabled:
        logger.info(f"[SMS MOCK] → {phone}: {message[:80]}...")
        return True

    if not settings.sms_api_key:
        logger.warning("SMS not configured. Set SMS_API_KEY.")
        return False

    phone = phone.replace("+91", "").replace("+", "").replace(" ", "")[-10:]

    url = "https://www.fast2sms.com/dev/bulkV2"
    params = {
        "authorization": settings.sms_api_key,
        "sender_id":     settings.sms_sender_id,
        "message":       message[:160],   # SMS limit
        "language":      "english",
        "route":         "dlt",
        "numbers":       phone,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            if data.get("return"):
                logger.info(f"[SMS] Sent to {phone[-4:]}**** ✓")
                return True
            else:
                logger.error(f"[SMS] Failed: {data}")
                return False
    except Exception as e:
        logger.error(f"[SMS] Exception: {e}")
        return False


# ─── Unified dispatcher ───────────────────────────────────────────────────────

async def dispatch_alert(
    facility_id: str,
    facility_name: str,
    owner_phone: str,
    severity: str,
    message_en: str,
    message_hi: str,
    message_mr: str,
) -> dict:
    """
    Main entry point. Called after an alert is saved to DB.

    Strategy:
    - Skip if on cooldown (prevents alert fatigue)
    - Try WhatsApp first in Marathi (most farmers prefer it)
    - Fall back to SMS if WhatsApp fails
    - Log everything
    """
    settings = get_settings()

    # Skip non-critical if notify_critical_only is set
    if settings.notify_critical_only and severity != "critical":
        logger.debug(f"Skipping non-critical alert for {facility_name}")
        return {"sent": False, "reason": "non_critical_skipped"}

    # Cooldown check
    if _is_on_cooldown(facility_id):
        logger.info(f"[Notify] {facility_name} on cooldown — skipping")
        return {"sent": False, "reason": "cooldown"}

    # Pick best message language (Marathi for Maharashtra, Hindi fallback)
    message = message_mr if message_mr != message_en else (
        message_hi if message_hi != message_en else message_en
    )

    # Build a clean SMS-friendly message (strip emojis for SMS)
    sms_message = f"ColdGuard Alert [{facility_name}]\n{message_en}\nPowered by ColdGuard"

    results = {"whatsapp": False, "sms": False}

    # 1. Try WhatsApp
    wa_ok = await send_whatsapp(
        phone=owner_phone,
        message=f"🌡️ *ColdGuard Alert*\n*{facility_name}*\n\n{message}\n\n_{message_en}_",
        language="mr",
        facility_name=facility_name,
        severity=severity,
    )
    results["whatsapp"] = wa_ok

    # 2. SMS — always send for critical, fallback for others
    if severity == "critical" or not wa_ok:
        sms_ok = await send_sms(phone=owner_phone, message=sms_message)
        results["sms"] = sms_ok

    if results["whatsapp"] or results["sms"]:
        _mark_notified(facility_id)

    logger.info(f"[Notify] {facility_name} | WA:{results['whatsapp']} SMS:{results['sms']}")
    return {"sent": True, "channels": results}


def print_setup_guide():
    """Print setup instructions to logs on startup."""
    logger.info("""
╔══════════════════════════════════════════════════════════╗
║           WHATSAPP + SMS SETUP GUIDE                     ║
╠══════════════════════════════════════════════════════════╣
║  WhatsApp Business API (Meta):                           ║
║  1. Go to developers.facebook.com                        ║
║  2. Create App → Business → WhatsApp                     ║
║  3. Get Phone Number ID and Permanent Token              ║
║  4. Add to .env:                                         ║
║     WHATSAPP_ENABLED=true                                ║
║     WHATSAPP_TOKEN=your_token_here                       ║
║     WHATSAPP_PHONE_ID=your_phone_id_here                 ║
║                                                          ║
║  SMS via fast2sms.com (Free tier: 500 SMS/day):          ║
║  1. Sign up at fast2sms.com                              ║
║  2. Get API key from Dashboard → Dev API                 ║
║  3. Add to .env:                                         ║
║     SMS_ENABLED=true                                     ║
║     SMS_API_KEY=your_key_here                            ║
║                                                          ║
║  Until configured: alerts are LOGGED (mock mode)         ║
╚══════════════════════════════════════════════════════════╝
    """)
