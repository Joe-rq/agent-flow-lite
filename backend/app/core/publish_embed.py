from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TypedDict, cast

from filelock import BaseFileLock

from app.core.paths import BACKEND_DATA_DIR


EMBED_TOKEN_TTL_HOURS = 24
EMBED_TOKEN_TTL = timedelta(hours=EMBED_TOKEN_TTL_HOURS)


class _EmbedTokenEntry(TypedDict):
    workflow_id: str
    created_at: str
    expires_at: str
    created_by: str


class _EmbedTokenStore(TypedDict):
    tokens: dict[str, _EmbedTokenEntry]


class EmbedTokenError(Exception):
    pass


class EmbedTokenNotFound(EmbedTokenError):
    pass


class EmbedTokenExpired(EmbedTokenError):
    pass


@dataclass(frozen=True)
class EmbedTokenRecord:
    token: str
    workflow_id: str
    created_at: datetime
    expires_at: datetime
    created_by: str

    def expires_at_iso(self) -> str:
        return ensure_utc_datetime(self.expires_at).isoformat()


def ensure_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _store_path() -> Path:
    return BACKEND_DATA_DIR / "embed_tokens.json"


def _lock_for(path: Path) -> BaseFileLock:
    from filelock import FileLock

    return FileLock(str(path) + ".lock")


def _ensure_data_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _coerce_entry(raw: object) -> _EmbedTokenEntry | None:
    if not isinstance(raw, dict):
        return None
    raw_map = cast(dict[object, object], raw)
    if not all(isinstance(k, str) for k in raw_map.keys()):
        return None
    mapped = cast(dict[str, object], raw_map)

    workflow_id = mapped.get("workflow_id")
    created_at = mapped.get("created_at")
    expires_at = mapped.get("expires_at")
    created_by = mapped.get("created_by")
    if not (
        isinstance(workflow_id, str)
        and isinstance(created_at, str)
        and isinstance(expires_at, str)
        and isinstance(created_by, str)
    ):
        return None
    return {
        "workflow_id": workflow_id,
        "created_at": created_at,
        "expires_at": expires_at,
        "created_by": created_by,
    }


def _load_store_unlocked(path: Path) -> _EmbedTokenStore:
    _ensure_data_dir(path)
    if not path.exists():
        return {"tokens": {}}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data_obj = cast(object, json.load(handle))
        if not isinstance(data_obj, dict):
            return {"tokens": {}}
        raw_dict = cast(dict[object, object], data_obj)
        data_map: dict[str, object] = {
            k: v for k, v in raw_dict.items() if isinstance(k, str)
        }
        tokens_obj = data_map.get("tokens")
        if not isinstance(tokens_obj, dict):
            return {"tokens": {}}

        tokens: dict[str, _EmbedTokenEntry] = {}
        tokens_raw = cast(dict[object, object], tokens_obj)
        for key, value in tokens_raw.items():
            if not isinstance(key, str):
                continue
            entry = _coerce_entry(value)
            if entry is None:
                continue
            tokens[key] = entry

        return {"tokens": tokens}
    except (OSError, json.JSONDecodeError):
        return {"tokens": {}}


def _atomic_write(path: Path, data: _EmbedTokenStore) -> None:
    _ensure_data_dir(path)
    tmp_path = path.with_name(path.name + f".tmp.{uuid.uuid4().hex}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


def create_embed_token(*, workflow_id: str, created_by: int | str) -> EmbedTokenRecord:
    token = str(uuid.uuid4())
    now = _now_utc()
    expires_at = now + EMBED_TOKEN_TTL
    record = EmbedTokenRecord(
        token=token,
        workflow_id=workflow_id,
        created_at=now,
        expires_at=expires_at,
        created_by=str(created_by),
    )

    path = _store_path()
    lock = _lock_for(path)
    with lock:
        data = _load_store_unlocked(path)
        tokens = data["tokens"]
        tokens[token] = {
            "workflow_id": workflow_id,
            "created_at": record.created_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "created_by": record.created_by,
        }
        _atomic_write(path, data)

    return record


def _parse_record(token: str, raw: _EmbedTokenEntry) -> EmbedTokenRecord:
    workflow_id = raw["workflow_id"].strip()
    created_at_raw = raw["created_at"].strip()
    expires_at_raw = raw["expires_at"].strip()
    created_by = raw["created_by"].strip() or "anonymous"
    if not workflow_id or not created_at_raw or not expires_at_raw:
        raise EmbedTokenNotFound(token)

    try:
        created_at = ensure_utc_datetime(datetime.fromisoformat(created_at_raw))
        expires_at = ensure_utc_datetime(datetime.fromisoformat(expires_at_raw))
    except ValueError as exc:
        raise EmbedTokenNotFound(token) from exc
    return EmbedTokenRecord(
        token=token,
        workflow_id=workflow_id,
        created_at=created_at,
        expires_at=expires_at,
        created_by=created_by,
    )


def get_valid_embed_record(token: str) -> EmbedTokenRecord:
    path = _store_path()
    lock = _lock_for(path)
    with lock:
        data = _load_store_unlocked(path)
    raw = data["tokens"].get(token)
    if raw is None:
        raise EmbedTokenNotFound(token)
    record = _parse_record(token, raw)
    if record.expires_at <= _now_utc():
        raise EmbedTokenExpired(token)
    return record
