"""
Auth API
Handles all authentication flows:
  - Admin/Operator: Email + Password (+ Google OAuth for Admin)
  - Farmer: Phone OTP via SMS
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import asyncpg
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.config import get_settings
from app.core.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, hash_token,
    generate_otp, verify_otp_hash,
)
from app.core.dependencies import get_current_user

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "operator"   # operator | admin

class OTPRequestBody(BaseModel):
    phone: str
    name: Optional[str] = None   # required on first login (auto-register)

class OTPVerifyBody(BaseModel):
    phone: str
    otp: str

class RefreshBody(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _issue_tokens(conn: asyncpg.Connection, user: dict) -> dict:
    """Create access + refresh tokens, store refresh hash in DB."""
    settings = get_settings()
    access = create_access_token(str(user["id"]), user["role"], user["name"])
    raw_refresh, hashed_refresh = create_refresh_token()

    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    await conn.execute("""
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
        VALUES ($1, $2, $3)
    """, user["id"], hashed_refresh, expires)

    await conn.execute(
        "UPDATE users SET last_login = NOW() WHERE id = $1", user["id"]
    )

    return {
        "access_token":  access,
        "refresh_token": raw_refresh,
        "token_type":    "bearer",
        "user": {
            "id":   str(user["id"]),
            "name": user["name"],
            "role": user["role"],
            "email": user.get("email"),
            "phone": user.get("phone"),
        }
    }


# ─── Email / Password ─────────────────────────────────────────────────────────

@router.post("/register", summary="Register operator or admin")
async def register(req: RegisterRequest, conn: asyncpg.Connection = Depends(get_db)):
    if req.role not in ("operator", "admin"):
        raise HTTPException(400, "Role must be 'operator' or 'admin'")

    existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", req.email)
    if existing:
        raise HTTPException(400, "Email already registered")

    user = await conn.fetchrow("""
        INSERT INTO users (email, name, role, password_hash)
        VALUES ($1, $2, $3, $4)
        RETURNING id, email, phone, name, role
    """, req.email, req.name, req.role, hash_password(req.password))

    return await _issue_tokens(conn, dict(user))


@router.post("/login", summary="Email + password login (Admin/Operator)")
async def login(req: EmailLoginRequest, conn: asyncpg.Connection = Depends(get_db)):
    user = await conn.fetchrow(
        "SELECT * FROM users WHERE email = $1 AND active = TRUE", req.email
    )
    if not user or not user["password_hash"]:
        raise HTTPException(401, "Invalid credentials")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    return await _issue_tokens(conn, dict(user))


# ─── Phone OTP (Farmer) ───────────────────────────────────────────────────────

@router.post("/otp/request", summary="Request OTP (Farmer phone login)")
async def request_otp(req: OTPRequestBody, conn: asyncpg.Connection = Depends(get_db)):
    settings = get_settings()
    phone = req.phone.strip().replace(" ", "")

    # Auto-register farmer if first time
    user = await conn.fetchrow("SELECT id FROM users WHERE phone = $1", phone)
    if not user:
        if not req.name:
            raise HTTPException(400, "Name required for first-time registration")
        await conn.execute("""
            INSERT INTO users (phone, name, role)
            VALUES ($1, $2, 'farmer')
            ON CONFLICT (phone) DO NOTHING
        """, phone, req.name)

    # Generate OTP
    raw_otp, otp_hash = generate_otp()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)

    await conn.execute("""
        INSERT INTO phone_otps (phone, otp_hash, expires_at, attempts)
        VALUES ($1, $2, $3, 0)
        ON CONFLICT (phone) DO UPDATE
            SET otp_hash = $2, expires_at = $3, attempts = 0
    """, phone, otp_hash, expires)

    # Send OTP via SMS
    try:
        from app.services.notification_service import send_sms
        await send_sms(phone, f"ColdGuard OTP: {raw_otp}. Valid for {settings.otp_expire_minutes} mins. Do not share.")
    except Exception:
        pass

    # In dev/mock mode always return OTP in response for testing
    import os
    response = {"message": "OTP sent", "expires_minutes": settings.otp_expire_minutes}
    if not settings.sms_enabled:
        response["dev_otp"] = raw_otp   # remove this in production!
    return response


@router.post("/otp/verify", summary="Verify OTP and get tokens")
async def verify_otp(req: OTPVerifyBody, conn: asyncpg.Connection = Depends(get_db)):
    settings = get_settings()
    phone = req.phone.strip().replace(" ", "")

    record = await conn.fetchrow(
        "SELECT * FROM phone_otps WHERE phone = $1", phone
    )
    if not record:
        raise HTTPException(401, "No OTP requested for this number")

    # Check expiry
    if datetime.now(timezone.utc) > record["expires_at"].replace(tzinfo=timezone.utc):
        raise HTTPException(401, "OTP expired. Request a new one.")

    # Check attempts
    if record["attempts"] >= settings.otp_max_attempts:
        raise HTTPException(429, "Too many attempts. Request a new OTP.")

    await conn.execute(
        "UPDATE phone_otps SET attempts = attempts + 1 WHERE phone = $1", phone
    )

    if not verify_otp_hash(req.otp, record["otp_hash"]):
        raise HTTPException(401, "Invalid OTP")

    # Clean up used OTP
    await conn.execute("DELETE FROM phone_otps WHERE phone = $1", phone)

    user = await conn.fetchrow(
        "SELECT * FROM users WHERE phone = $1 AND active = TRUE", phone
    )
    if not user:
        raise HTTPException(401, "User not found")

    return await _issue_tokens(conn, dict(user))


# ─── Token Refresh ────────────────────────────────────────────────────────────

@router.post("/refresh", summary="Refresh access token")
async def refresh_token(req: RefreshBody, conn: asyncpg.Connection = Depends(get_db)):
    token_hash = hash_token(req.refresh_token)
    record = await conn.fetchrow("""
        SELECT rt.*, u.id as uid, u.name, u.role, u.email, u.phone, u.active
        FROM refresh_tokens rt
        JOIN users u ON u.id = rt.user_id
        WHERE rt.token_hash = $1
    """, token_hash)

    if not record:
        raise HTTPException(401, "Invalid refresh token")
    if datetime.now(timezone.utc) > record["expires_at"].replace(tzinfo=timezone.utc):
        raise HTTPException(401, "Refresh token expired. Please login again.")
    if not record["active"]:
        raise HTTPException(401, "User inactive")

    # Rotate refresh token
    await conn.execute("DELETE FROM refresh_tokens WHERE token_hash = $1", token_hash)

    user = {"id": record["uid"], "name": record["name"], "role": record["role"],
            "email": record["email"], "phone": record["phone"]}
    return await _issue_tokens(conn, user)


# ─── Google OAuth ─────────────────────────────────────────────────────────────

@router.get("/google", summary="Start Google OAuth flow (Admin only)")
async def google_login(request: Request):
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(501, "Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")

    from authlib.integrations.starlette_client import OAuth
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    redirect_uri = f"{settings.api_url}/api/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", summary="Google OAuth callback")
async def google_callback(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(501, "Google OAuth not configured")

    from authlib.integrations.starlette_client import OAuth
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.google.userinfo(token=token)

    google_sub = userinfo["sub"]
    email      = userinfo.get("email")
    name       = userinfo.get("name", email)

    # Upsert user
    user = await conn.fetchrow("""
        INSERT INTO users (email, name, role, google_sub)
        VALUES ($1, $2, 'admin', $3)
        ON CONFLICT (google_sub) DO UPDATE
            SET email = $1, name = $2, last_login = NOW()
        RETURNING *
    """, email, name, google_sub)

    tokens = await _issue_tokens(conn, dict(user))

    # Redirect to frontend with tokens in query params
    frontend_url = "http://localhost:5173"
    return RedirectResponse(
        f"{frontend_url}/auth/callback?"
        f"access_token={tokens['access_token']}&"
        f"refresh_token={tokens['refresh_token']}&"
        f"role={user['role']}"
    )


# ─── Profile + Logout ─────────────────────────────────────────────────────────

@router.get("/me", summary="Get current user profile")
async def get_me(user: dict = Depends(get_current_user)):
    return {k: v for k, v in user.items() if k != "password_hash"}


@router.post("/logout", summary="Revoke refresh token")
async def logout(req: RefreshBody, conn: asyncpg.Connection = Depends(get_db)):
    token_hash = hash_token(req.refresh_token)
    await conn.execute("DELETE FROM refresh_tokens WHERE token_hash = $1", token_hash)
    return {"logged_out": True}
