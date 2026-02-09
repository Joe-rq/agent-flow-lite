"""
Authentication utilities and FastAPI dependencies.

Provides token validation, user retrieval, and dependency injection for protected endpoints.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import AuthToken, User, UserRole


def normalize_email(email: str) -> str:
    """Normalize email address: lowercase and strip whitespace."""
    return email.lower().strip()


async def get_or_create_user(
    db: AsyncSession,
    email: str
) -> User:
    """
    Get existing user or create new user if not exists.
    
    Auto-assigns admin role if email matches ADMIN_EMAIL setting.
    Soft-deleted users are treated as non-existent (new user created).
    
    Args:
        db: Database session
        email: User email address
        
    Returns:
        User: Existing or newly created user
    """
    normalized_email = normalize_email(email)
    
    # Check for existing active user
    result = await db.execute(
        select(User).where(
            User.email == normalized_email,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if user:
        return user
    
    # Determine role based on admin email
    admin_email = settings().admin_email
    role = UserRole.ADMIN if normalized_email == admin_email else UserRole.USER
    
    # Create new user
    user = User(email=normalized_email, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def create_auth_token(
    db: AsyncSession,
    user_id: int
) -> AuthToken:
    """
    Create a new authentication token for user.
    
    Token expires after 7 days.
    
    Args:
        db: Database session
        user_id: User ID to create token for
        
    Returns:
        AuthToken: Created auth token
    """
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    token = AuthToken(
        token=str(uuid4()),
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    
    return token


async def get_user_by_token(
    db: AsyncSession,
    token_str: str
) -> Optional[User]:
    """
    Get user by authentication token.
    
    Validates token exists, is not expired, and user is not soft deleted.
    Does NOT check is_active - that's handled separately for proper 403 response.
    
    Args:
        db: Database session
        token_str: Token string
        
    Returns:
        User: User if token valid, None otherwise
    """
    result = await db.execute(
        select(AuthToken).where(AuthToken.token == token_str)
    )
    token = result.scalar_one_or_none()
    
    if not token:
        return None
    
    if token.is_expired:
        return None
    
    # Load user and check status
    result = await db.execute(
        select(User).where(User.id == token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # Only check soft delete, not is_active (handled in get_current_user for 403)
    if user.is_deleted:
        return None
    
    return user


async def delete_auth_token(
    db: AsyncSession,
    token_str: str
) -> bool:
    """
    Delete authentication token (logout).
    
    Args:
        db: Database session
        token_str: Token string to delete
        
    Returns:
        bool: True if token was found and deleted
    """
    result = await db.execute(
        select(AuthToken).where(AuthToken.token == token_str)
    )
    token = result.scalar_one_or_none()
    
    if not token:
        return False
    
    await db.delete(token)
    await db.commit()
    
    return True


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Delete all expired authentication tokens.
    
    Should be called periodically (e.g., by a scheduled job) to prevent
    token table bloat.
    
    Args:
        db: Database session
        
    Returns:
        int: Number of expired tokens deleted
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AuthToken).where(AuthToken.expires_at < now)
    )
    expired_tokens = result.scalars().all()
    
    count = 0
    for token in expired_tokens:
        await db.delete(token)
        count += 1
    
    if count > 0:
        await db.commit()
    
    return count


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Extracts Bearer token from Authorization header and validates it.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User: Authenticated user
        
    Raises:
        HTTPException: 401 if no/invalid token, 403 if user inactive
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
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user
