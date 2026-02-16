"""
Authentication API endpoints.

Provides register, login, logout, and user info endpoints.
"""

import re
from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    authenticate_user,
    create_auth_token,
    delete_auth_token,
    get_current_user,
    get_user_by_token,
    normalize_email,
    register_user,
)
from app.core.audit import audit_log
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
MIN_PASSWORD_LENGTH = 6
_failed_logins: dict[str, list[datetime]] = {}
_failed_logins_lock = Lock()


class RegisterRequest(BaseModel):
    """Register request model."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginRequest(BaseModel):
    """Login request model."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """User response model."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role (admin or user)")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: str = Field(..., description="Creation timestamp ISO format")

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Login response model."""

    token: str = Field(..., description="Authentication token")
    user: UserResponse = Field(..., description="User information")


class LogoutResponse(BaseModel):
    """Logout response model."""

    success: bool = Field(..., description="Whether logout was successful")


def _validate_email(email: str) -> None:
    """Validate email format, raise HTTPException on failure."""
    if not email or not re.match(EMAIL_PATTERN, email.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid email address required",
        )


def _validate_password(password: str) -> None:
    """Validate password, raise HTTPException on failure."""
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
        )


def _user_response(user: User) -> UserResponse:
    """Build UserResponse from User model."""
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


def _failed_login_window(email: str) -> int:
    s = settings()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=s.auth_lock_window_minutes)
    with _failed_logins_lock:
        attempts = [ts for ts in _failed_logins.get(email, []) if ts >= cutoff]
        _failed_logins[email] = attempts
        return len(attempts)


def _get_retry_after_seconds(email: str) -> int:
    s = settings()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=s.auth_lock_window_minutes)
    with _failed_logins_lock:
        attempts = [ts for ts in _failed_logins.get(email, []) if ts >= cutoff]
        if len(attempts) < s.auth_lock_max_attempts:
            _failed_logins[email] = attempts
            return 0
        earliest = min(attempts)
        unlock_at = earliest + timedelta(minutes=s.auth_lock_window_minutes)
        remaining = int((unlock_at - now).total_seconds())
        _failed_logins[email] = attempts
        return max(1, remaining)


def _record_failed_login(email: str) -> None:
    now = datetime.now(timezone.utc)
    _failed_login_window(email)
    with _failed_logins_lock:
        attempts = _failed_logins.get(email, [])
        attempts.append(now)
        _failed_logins[email] = attempts


def _clear_failed_logins(email: str) -> None:
    with _failed_logins_lock:
        if email in _failed_logins:
            del _failed_logins[email]


@router.post("/register", response_model=LoginResponse)
async def register(
    request: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Register a new user with email and password.

    Returns auth token and user info on success.
    """
    _validate_email(request.email)
    _validate_password(request.password)

    try:
        user = await register_user(db, request.email, request.password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    token = await create_auth_token(db, user.id)

    return LoginResponse(token=token.token, user=_user_response(user))


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Login with email and password.

    Returns auth token and user info.
    """
    _validate_email(payload.email)
    normalized_email = normalize_email(payload.email)

    if not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required"
        )

    retry_after = _get_retry_after_seconds(normalized_email)
    if retry_after > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        _record_failed_login(normalized_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    _clear_failed_logins(normalized_email)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    token = await create_auth_token(db, user.id)

    audit_log(
        request=request,
        user_id=user.id,
        action="login",
        resource_id=f"user:{user.id}",
    )

    return LoginResponse(token=token.token, user=_user_response(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user info.

    Requires Bearer token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request, db: AsyncSession = Depends(get_db)
) -> LogoutResponse:
    """
    Logout endpoint - invalidates the auth token.

    Requires Bearer token in Authorization header.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_str = auth_header[7:]  # Remove "Bearer " prefix

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_token(db, token_str)

    # Delete the token
    deleted = await delete_auth_token(db, token_str)

    if deleted and user is not None:
        audit_log(
            request=request,
            user_id=user.id,
            action="logout",
            resource_id=f"user:{user.id}",
        )

    return LogoutResponse(success=deleted)
