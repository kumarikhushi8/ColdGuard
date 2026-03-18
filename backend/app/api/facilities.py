from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def list_facilities(conn: asyncpg.Connection = Depends(get_db)):
    rows = await conn.fetch("SELECT * FROM facilities ORDER BY name")
    return [dict(r) for r in rows]

@router.get("/{facility_id}")
async def get_facility(facility_id: str, conn: asyncpg.Connection = Depends(get_db)):
    row = await conn.fetchrow("SELECT * FROM facilities WHERE id = $1", facility_id)
    if not row:
        raise HTTPException(404, "Facility not found")
    return dict(row)
