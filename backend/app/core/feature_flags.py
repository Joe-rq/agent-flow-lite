from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.setting import Setting

FEATURE_FLAG_KEYS = (
    "ENABLE_CODE_NODE",
    "ENABLE_HTTP_NODE",
    "ENABLE_OPENAI_API",
    "ENABLE_PUBLIC_EMBED",
)


def _normalize_flag_key(flag_key: str) -> str:
    key = flag_key.strip().upper()
    if key not in FEATURE_FLAG_KEYS:
        raise ValueError(f"Unsupported feature flag: {flag_key}")
    return key


def _setting_key(flag_key: str) -> str:
    return f"feature_flag:{flag_key}"


def _default_feature_flags() -> dict[str, bool]:
    s = settings()
    return {
        "ENABLE_CODE_NODE": bool(s.enable_code_node),
        "ENABLE_HTTP_NODE": bool(s.enable_http_node),
        "ENABLE_OPENAI_API": bool(s.enable_openai_api),
        "ENABLE_PUBLIC_EMBED": bool(s.enable_public_embed),
    }


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


async def get_feature_flag_value(db: AsyncSession, flag_key: str) -> bool:
    key = _normalize_flag_key(flag_key)
    result = await db.execute(select(Setting).where(Setting.key == _setting_key(key)))
    row = result.scalar_one_or_none()
    if row is None:
        return _default_feature_flags()[key]
    return _parse_bool(row.value)


async def list_feature_flags(db: AsyncSession) -> dict[str, bool]:
    defaults = _default_feature_flags()
    rows = await db.execute(
        select(Setting).where(
            Setting.key.in_([_setting_key(flag) for flag in FEATURE_FLAG_KEYS])
        )
    )
    mapped = {row.key: row.value for row in rows.scalars().all()}
    for flag_key in FEATURE_FLAG_KEYS:
        setting_key = _setting_key(flag_key)
        if setting_key in mapped:
            defaults[flag_key] = _parse_bool(mapped[setting_key])
    return defaults


async def set_feature_flag_value(
    db: AsyncSession, flag_key: str, enabled: bool
) -> bool:
    key = _normalize_flag_key(flag_key)
    setting_key = _setting_key(key)
    result = await db.execute(select(Setting).where(Setting.key == setting_key))
    row = result.scalar_one_or_none()
    if row is None:
        row = Setting(key=setting_key, value="true" if enabled else "false")
        db.add(row)
    else:
        row.value = "true" if enabled else "false"
    await db.commit()
    return enabled


async def is_feature_enabled(flag_key: str) -> bool:
    async with AsyncSessionLocal() as db:
        return await get_feature_flag_value(db, flag_key)
