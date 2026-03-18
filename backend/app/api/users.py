"""
Users API
Admin-only endpoints for managing operators, farmers, and facility assignments.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncpg
from app.core.database import get_db
from app.core.dependencies import require_admin, require_operator, get_operator_facilities
from app.core.auth import hash_password

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    name: str
    role: str
    password: Optional[str] = None

class AssignFacilityRequest(BaseModel):
    user_id: str
    facility_id: str
    crop: Optional[str] = None   # for farmers


@router.get("/", summary="List all users (admin only)")
async def list_users(
    role: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    filters = ["1=1"]
    params = []
    if role:
        params.append(role)
        filters.append(f"role = ${len(params)}")

    rows = await conn.fetch(f"""
        SELECT id, email, phone, name, role, active, created_at, last_login
        FROM users
        WHERE {' AND '.join(filters)}
        ORDER BY role, name
    """, *params)
    return [dict(r) for r in rows]


@router.post("/", summary="Create operator or farmer (admin only)")
async def create_user(
    req: CreateUserRequest,
    conn: asyncpg.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    if req.role not in ("operator", "farmer", "admin"):
        raise HTTPException(400, "Invalid role")

    pw_hash = hash_password(req.password) if req.password else None

    user = await conn.fetchrow("""
        INSERT INTO users (email, phone, name, role, password_hash)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, email, phone, name, role, active, created_at
    """, req.email, req.phone, req.name, req.role, pw_hash)
    return dict(user)


@router.patch("/{user_id}/activate", summary="Activate/deactivate user")
async def toggle_active(
    user_id: str,
    active: bool,
    conn: asyncpg.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    await conn.execute("UPDATE users SET active = $1 WHERE id = $2", active, user_id)
    return {"updated": True, "active": active}


@router.patch("/{user_id}/password", summary="Reset user password")
async def reset_password(
    user_id: str,
    new_password: str,
    conn: asyncpg.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE id = $2",
        hash_password(new_password), user_id
    )
    return {"updated": True}


# ─── Facility assignments ──────────────────────────────────────────────────────

@router.post("/assign-facility", summary="Assign facility to operator or farmer")
async def assign_facility(
    req: AssignFacilityRequest,
    conn: asyncpg.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    user = await conn.fetchrow("SELECT role FROM users WHERE id = $1", req.user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if user["role"] == "operator":
        await conn.execute("""
            INSERT INTO operator_facilities (user_id, facility_id)
            VALUES ($1, $2) ON CONFLICT DO NOTHING
        """, req.user_id, req.facility_id)
    elif user["role"] == "farmer":
        await conn.execute("""
            INSERT INTO farmer_facilities (user_id, facility_id, crop)
            VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
        """, req.user_id, req.facility_id, req.crop)
    else:
        raise HTTPException(400, "Admins have access to all facilities")

    return {"assigned": True}


@router.delete("/unassign-facility", summary="Remove facility assignment")
async def unassign_facility(
    user_id: str,
    facility_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    _: dict = Depends(require_admin),
):
    await conn.execute(
        "DELETE FROM operator_facilities WHERE user_id=$1 AND facility_id=$2",
        user_id, facility_id
    )
    await conn.execute(
        "DELETE FROM farmer_facilities WHERE user_id=$1 AND facility_id=$2",
        user_id, facility_id
    )
    return {"removed": True}


@router.get("/{user_id}/facilities", summary="Get facilities for a user")
async def user_facilities(
    user_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(require_operator),
):
    user = await conn.fetchrow("SELECT role FROM users WHERE id = $1", user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if user["role"] == "operator":
        rows = await conn.fetch("""
            SELECT f.id, f.name, f.location FROM facilities f
            JOIN operator_facilities of ON of.facility_id = f.id
            WHERE of.user_id = $1
        """, user_id)
    else:
        rows = await conn.fetch("""
            SELECT f.id, f.name, f.location, ff.crop FROM facilities f
            JOIN farmer_facilities ff ON ff.facility_id = f.id
            WHERE ff.user_id = $1
        """, user_id)

    return [dict(r) for r in rows]


@router.get("/me/facilities", summary="Get my assigned facilities")
async def my_facilities(
    current_user: dict = Depends(require_operator),
    conn: asyncpg.Connection = Depends(get_db),
):
    facility_ids = await get_operator_facilities(current_user, conn)
    if not facility_ids:
        return []
    rows = await conn.fetch(
        "SELECT id, name, location, capacity_mt FROM facilities WHERE id = ANY($1::uuid[])",
        facility_ids
    )
    return [dict(r) for r in rows]
