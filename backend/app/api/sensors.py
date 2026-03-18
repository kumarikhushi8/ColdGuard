from fastapi import APIRouter, Depends
import asyncpg
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def list_sensors(conn: asyncpg.Connection = Depends(get_db)):
    rows = await conn.fetch("""
        SELECT s.*, f.name as facility_name
        FROM sensors s JOIN facilities f ON f.id = s.facility_id
        ORDER BY f.name, s.sensor_code
    """)
    return [dict(r) for r in rows]

@router.get("/{sensor_id}/latest")
async def latest_reading(sensor_id: str, conn: asyncpg.Connection = Depends(get_db)):
    row = await conn.fetchrow("""
        SELECT * FROM sensor_readings
        WHERE sensor_id = $1
        ORDER BY time DESC LIMIT 1
    """, sensor_id)
    return dict(row) if row else {}
