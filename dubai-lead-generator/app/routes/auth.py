"""
Authentication API endpoints for LITSA Lead Generator.
Provides secure login, session verification, and token refresh.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.utils.auth import (
    verify_password,
    create_access_token,
    get_admin_credentials,
    get_current_admin,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: dict


@router.post("/login", response_model=LoginResponse)
def admin_login(payload: LoginRequest):
    """Authenticate administrator and return signed JWT."""
    admin_email, admin_hash = get_admin_credentials()

    input_email = payload.email.strip().lower()
    if input_email != admin_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(payload.password, admin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.config import settings
    token = create_access_token({"sub": admin_email, "role": "admin"})

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": settings.jwt_expire_minutes,
        "user": {"email": admin_email, "role": "admin"},
    }


@router.get("/me")
def get_current_user_profile(user: dict = Depends(get_current_admin)):
    """Retrieve active session profile."""
    email = user.get("sub") or user.get("email")
    return {
        "status": "authenticated",
        "user": {**user, "email": email},
    }


@router.post("/logout")
def logout_user(user: dict = Depends(get_current_admin)):
    """Acknowledge logout (client drops token)."""
    return {"status": "success", "message": "Logged out successfully."}
