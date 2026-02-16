from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import Request

from app.core.paths import BACKEND_DATA_DIR

logger = logging.getLogger(__name__)

AUDIT_LOG_FILE = BACKEND_DATA_DIR / "audit.log"
REQUIRED_AUDIT_FIELDS = ("timestamp", "user_id", "action", "resource_id", "ip")

_audit_lock = Lock()


def _ensure_audit_dir() -> None:
    AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def build_audit_entry(
    *,
    user_id: int | str | None,
    action: str,
    resource_id: str,
    ip: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user_id) if user_id is not None else "anonymous",
        "action": action,
        "resource_id": resource_id,
        "ip": ip,
    }
    if extra:
        entry.update(extra)
    return entry


def write_audit_entry(entry: dict[str, Any]) -> None:
    _ensure_audit_dir()
    try:
        with _audit_lock:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.warning("Failed to write audit log", exc_info=True)


def audit_log(
    *,
    request: Request,
    user_id: int | str | None,
    action: str,
    resource_id: str,
    extra: dict[str, Any] | None = None,
) -> None:
    ip = request.client.host if request.client else "unknown"
    entry = build_audit_entry(
        user_id=user_id,
        action=action,
        resource_id=resource_id,
        ip=ip,
        extra=extra,
    )
    write_audit_entry(entry)
