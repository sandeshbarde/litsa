"""
Authentication and security module for LITSA Lead Generator.
Provides JWT issuance, bcrypt password hashing, and admin auth dependency.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.config import settings

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False


def get_admin_credentials() -> tuple[str, str]:
    """Retrieve configured admin email and password hash."""
    email = (settings.admin_email or "admin@litsa.io").strip().lower()
    p_hash = (settings.admin_password_hash or "").strip()
    if not p_hash:
        # Fallback to default password hash for first-time / development setup
        default_pwd = settings.admin_default_password or "Admin@Litsa2026!"
        p_hash = hash_password(default_pwd)
    return email, p_hash


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces admin authentication.
    Requires Authorization: Bearer <token>.
    """
    # In development mode without strict auth configured, allow graceful bypass if explicitly non-production
    if settings.app_env == "development" and not credentials and not settings.admin_password_hash:
        # Permissive dev mode: return mock admin user
        return {"sub": settings.admin_email, "role": "admin", "dev_mode": True}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Provide Bearer token in Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    admin_email, _ = get_admin_credentials()

    sub = str(payload.get("sub", "")).lower()
    if sub != admin_email and payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this administrative endpoint.",
        )

    return payload
