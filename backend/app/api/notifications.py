"""
Notifications API
Endpoints to test, configure, and manually trigger WhatsApp/SMS alerts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncpg
from app.core.database import get_db
from app.core.config import get_settings
from app.services.notification_service import send_whatsapp, send_sms, dispatch_alert

router = APIRouter()


class TestMessageRequest(BaseModel):
    phone: str
    channel: str = "whatsapp"   # "whatsapp" | "sms" | "both"
    message: str = "ColdGuard test message. Your cold storage monitoring is active."


class ManualAlertRequest(BaseModel):
    facility_id: str
    message: str
    severity: str = "warning"


@router.get("/status")
async def notification_status():
    """Check which notification channels are configured."""
    settings = get_settings()
    return {
        "whatsapp": {
            "enabled": settings.whatsapp_enabled,
            "configured": bool(settings.whatsapp_token and settings.whatsapp_phone_id),
            "phone_id": settings.whatsapp_phone_id[:8] + "..." if settings.whatsapp_phone_id else None,
        },
        "sms": {
            "enabled": settings.sms_enabled,
            "configured": bool(settings.sms_api_key),
            "sender_id": settings.sms_sender_id,
        },
        "settings": {
            "notify_critical_only": settings.notify_critical_only,
            "cooldown_minutes": settings.alert_cooldown_minutes,
        },
        "mode": "live" if (settings.whatsapp_enabled or settings.sms_enabled) else "mock",
    }


@router.post("/test")
async def send_test_message(req: TestMessageRequest):
    """
    Send a test WhatsApp/SMS to verify your credentials.
    Use this before going live.
    """
    results = {}

    if req.channel in ("whatsapp", "both"):
        results["whatsapp"] = await send_whatsapp(
            phone=req.phone,
            message=f"✅ *ColdGuard Test*\n{req.message}",
        )

    if req.channel in ("sms", "both"):
        results["sms"] = await send_sms(
            phone=req.phone,
            message=f"ColdGuard Test: {req.message}",
        )

    success = any(results.values())
    return {
        "success": success,
        "channels": results,
        "note": "Check logs if mock mode — set WHATSAPP_ENABLED=true to go live",
    }


@router.post("/send-alert")
async def manual_alert(
    req: ManualAlertRequest,
    conn: asyncpg.Connection = Depends(get_db),
):
    """Manually trigger a notification for a facility (useful for testing/demos)."""
    facility = await conn.fetchrow(
        "SELECT id, name, owner_phone FROM facilities WHERE id = $1",
        req.facility_id
    )
    if not facility:
        raise HTTPException(404, "Facility not found")

    result = await dispatch_alert(
        facility_id=str(facility["id"]),
        facility_name=facility["name"],
        owner_phone=facility["owner_phone"],
        severity=req.severity,
        message_en=req.message,
        message_hi=req.message,
        message_mr=req.message,
    )

    return {
        "facility": facility["name"],
        "phone": facility["owner_phone"],
        "result": result,
    }


@router.get("/facilities")
async def facility_contacts(conn: asyncpg.Connection = Depends(get_db)):
    """List all facilities with their notification contact info."""
    rows = await conn.fetch("""
        SELECT f.id, f.name, f.location, f.owner_name, f.owner_phone,
               COUNT(a.id) FILTER (WHERE a.acknowledged = FALSE) as unacked_alerts
        FROM facilities f
        LEFT JOIN alerts a ON a.facility_id = f.id
        GROUP BY f.id
        ORDER BY f.name
    """)
    return [dict(r) for r in rows]


@router.patch("/facilities/{facility_id}/phone")
async def update_phone(
    facility_id: str,
    phone: str,
    conn: asyncpg.Connection = Depends(get_db),
):
    """Update farmer's phone number for notifications."""
    phone = phone.strip().replace(" ", "")
    await conn.execute(
        "UPDATE facilities SET owner_phone = $1 WHERE id = $2",
        phone, facility_id
    )
    return {"updated": True, "phone": phone}
