from fastapi import APIRouter, Depends
import asyncpg
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def list_alerts(acknowledged: bool = False, conn: asyncpg.Connection = Depends(get_db)):
    rows = await conn.fetch("""
        SELECT a.*, f.name as facility_name
        FROM alerts a JOIN facilities f ON f.id = a.facility_id
        WHERE a.acknowledged = $1
        ORDER BY a.created_at DESC LIMIT 50
    """, acknowledged)
    return [dict(r) for r in rows]

@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, conn: asyncpg.Connection = Depends(get_db)):
    await conn.execute("""
        UPDATE alerts SET acknowledged = TRUE, ack_at = NOW()
        WHERE id = $1
    """, alert_id)
    return {"acknowledged": True}
