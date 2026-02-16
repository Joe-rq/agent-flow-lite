from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_log
from app.core.auth import User, get_current_user
from app.core.database import get_db
from app.core.feature_flags import (
    FEATURE_FLAG_KEYS,
    list_feature_flags,
    set_feature_flag_value,
)
from app.models.user import UserRole

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class FeatureFlagUpdateRequest(BaseModel):
    enabled: bool = Field(..., description="Target feature flag state")


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


@router.get("/feature-flags")
async def get_feature_flags(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    flags = await list_feature_flags(db)
    return {
        "items": [{"key": key, "enabled": flags[key]} for key in FEATURE_FLAG_KEYS],
        "total": len(FEATURE_FLAG_KEYS),
    }


@router.put("/feature-flags/{flag_key}")
async def update_feature_flag(
    request: Request,
    flag_key: str,
    payload: FeatureFlagUpdateRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        enabled = await set_feature_flag_value(db, flag_key, payload.enabled)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_log(
        request=request,
        user_id=user.id,
        action="feature_flag_update",
        resource_id=f"{flag_key.upper()}:{str(enabled).lower()}",
    )
    return {"key": flag_key.upper(), "enabled": enabled}
