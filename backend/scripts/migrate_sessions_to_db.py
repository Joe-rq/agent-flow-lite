from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal, DATA_DIR
from app.models.session import ChatSessionDB


SESSIONS_DIR = DATA_DIR / "sessions"


def _read_session_files() -> list[tuple[str, dict[str, object]]]:
    if not SESSIONS_DIR.exists():
        return []
    records: list[tuple[str, dict[str, object]]] = []
    for path in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, dict):
            records.append((path.stem, payload))
    return records


def _normalize_timestamp(value: object) -> datetime | None:
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


async def migrate() -> int:
    rows = _read_session_files()
    migrated = 0
    async with AsyncSessionLocal() as db:
        for fallback_session_id, payload in rows:
            session_id = str(payload.get("session_id") or fallback_session_id)
            user_id = payload.get("user_id")
            kb_id = payload.get("kb_id")
            workflow_id = payload.get("workflow_id")
            messages = payload.get("messages")
            if not isinstance(messages, list):
                messages = []

            created_at = _normalize_timestamp(payload.get("created_at"))
            updated_at = _normalize_timestamp(payload.get("updated_at"))
            messages_json = json.dumps(messages, ensure_ascii=False)

            result = await db.execute(
                select(ChatSessionDB).where(ChatSessionDB.session_id == session_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(
                    ChatSessionDB(
                        session_id=session_id,
                        user_id=str(user_id) if user_id is not None else None,
                        kb_id=str(kb_id) if kb_id is not None else None,
                        workflow_id=str(workflow_id)
                        if workflow_id is not None
                        else None,
                        messages_json=messages_json,
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                )
                migrated += 1
                continue

            existing.user_id = str(user_id) if user_id is not None else existing.user_id
            existing.kb_id = str(kb_id) if kb_id is not None else None
            existing.workflow_id = str(workflow_id) if workflow_id is not None else None
            existing.messages_json = messages_json
            if created_at is not None:
                existing.created_at = created_at
            existing.updated_at = updated_at

        await db.commit()
    return migrated


def main() -> None:
    count = asyncio.run(migrate())
    print(f"migrated_sessions={count}")


if __name__ == "__main__":
    main()
