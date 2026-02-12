from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class UserListItem(BaseModel):
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role (admin or user)")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: str = Field(..., description="Creation timestamp ISO format")

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    users: List[UserListItem] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")


class UserActionResponse(BaseModel):
    success: bool = Field(..., description="Whether action was successful")
    message: str = Field(..., description="Action result message")


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> UserListResponse:
    result = await db.execute(
        select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    user_items = [
        UserListItem(
            id=user.id,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
        for user in users
    ]
    
    return UserListResponse(users=user_items, total=len(user_items))


@router.post("/users/{user_id}/disable", response_model=UserActionResponse)
async def disable_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> UserActionResponse:
    if admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable yourself"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already disabled"
        )
    
    user.is_active = False
    await db.commit()
    
    return UserActionResponse(
        success=True,
        message=f"User {user.email} has been disabled"
    )


@router.post("/users/{user_id}/enable", response_model=UserActionResponse)
async def enable_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> UserActionResponse:
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already enabled"
        )
    
    user.is_active = True
    await db.commit()
    
    return UserActionResponse(
        success=True,
        message=f"User {user.email} has been enabled"
    )


@router.delete("/users/{user_id}", response_model=UserActionResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> UserActionResponse:
    if admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    await db.commit()
    
    return UserActionResponse(
        success=True,
        message=f"User {user.email} has been deleted"
    )
