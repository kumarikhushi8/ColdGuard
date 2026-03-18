"""
Auth Dependencies
FastAPI Depends() helpers for protecting routes by role.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
import asyncpg
import uuid as _uuid
from app.core.auth import decode_access_token
from app.core.database import get_db

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    conn: asyncpg.Connection = Depends(get_db),
) -> dict:
    """Decode JWT and return user dict. Raises 401 if invalid."""
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    try:
        user_id = _uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

    user = await conn.fetchrow(
        "SELECT id, email, phone, name, role, active FROM users WHERE id = $1",
        user_id
    )
    if not user or not user["active"]:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return dict(user)


def require_role(*roles: str):
    """Factory: returns a dependency that enforces one of the given roles."""
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires role: {' or '.join(roles)}"
            )
        return user
    return _check

require_admin    = require_role("admin")
require_operator = require_role("admin", "operator")
require_any      = require_role("admin", "operator", "farmer")


async def get_operator_facilities(
    user: dict,
    conn: asyncpg.Connection,
) -> list[str]:
    """Return list of facility IDs this user can access."""
    if user["role"] == "admin":
        rows = await conn.fetch("SELECT id FROM facilities")
        return [str(r["id"]) for r in rows]
    if user["role"] == "operator":
        rows = await conn.fetch(
            "SELECT facility_id FROM operator_facilities WHERE user_id = $1",
            user["id"]
        )
        return [str(r["facility_id"]) for r in rows]
    if user["role"] == "farmer":
        rows = await conn.fetch(
            "SELECT facility_id FROM farmer_facilities WHERE user_id = $1",
            user["id"]
        )
        return [str(r["facility_id"]) for r in rows]
    return []
