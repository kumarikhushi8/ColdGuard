from fastapi import APIRouter, Depends
import asyncpg
from app.core.database import get_db

router = APIRouter()

@router.get("/facility/{facility_id}")
async def facility_readings(facility_id: str, limit: int = 100, conn: asyncpg.Connection = Depends(get_db)):
    rows = await conn.fetch("""
        SELECT sr.*, s.sensor_code
        FROM sensor_readings sr
        JOIN sensors s ON s.id = sr.sensor_id
        WHERE s.facility_id = $1
        ORDER BY sr.time DESC LIMIT $2
    """, facility_id, limit)
    return [dict(r) for r in rows]
