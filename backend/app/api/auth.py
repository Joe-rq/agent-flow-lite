"""
Authentication API endpoints.

Provides login, logout, and user info endpoints.
"""
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_auth_token,
    delete_auth_token,
    get_current_user,
    get_or_create_user,
    normalize_email,
)
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request model."""
    email: str = Field(..., description="User email address")


class UserResponse(BaseModel):
    """User response model."""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role (admin or user)")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: str = Field(..., description="Creation timestamp ISO format")

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response model."""
    token: str = Field(..., description="Authentication token")
    user: UserResponse = Field(..., description="User information")


class LogoutResponse(BaseModel):
    """Logout response model."""
    success: bool = Field(..., description="Whether logout was successful")


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Login endpoint - creates user if not exists and returns auth token.
    
    - **email**: User email address
    
    Returns auth token and user info.
    """
    # Validate email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not request.email or not re.match(email_pattern, request.email.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid email address required"
        )
    
    # Normalize email
    normalized_email = normalize_email(request.email)
    
    # Get or create user
    user = await get_or_create_user(db, normalized_email)
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create auth token
    token = await create_auth_token(db, user.id)
    
    return LoginResponse(
        token=token.token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user info.
    
    Requires Bearer token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
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
    
    # Delete the token
    deleted = await delete_auth_token(db, token_str)
    
    return LogoutResponse(success=deleted)
