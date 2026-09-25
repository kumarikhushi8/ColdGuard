"""
Auth Core
JWT creation/verification, password hashing, OTP generation.
"""

import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
import bcrypt
from app.core.config import get_settings


# ─── Passwords ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ─── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, role: str, name: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "role": role, "name": name, "exp": expire, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, hashed_token). Store hash in DB, send raw to client."""
    raw = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed

def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


# ─── OTP ──────────────────────────────────────────────────────────────────────

def generate_otp() -> tuple[str, str]:
    """Returns (raw_6digit_otp, hashed). Send raw to user, store hash."""
    raw = str(secrets.randbelow(900000) + 100000)   # 100000–999999
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed

def verify_otp_hash(raw: str, stored_hash: str) -> bool:
    return hashlib.sha256(raw.encode()).hexdigest() == stored_hash

def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
