from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal, DATA_DIR
from app.models.workflow_db import WorkflowDB


WORKFLOW_FILE = DATA_DIR / "workflows.json"


def _parse_timestamp(value: object) -> datetime:
    if isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _normalize_items(raw: object) -> list[tuple[str, dict[str, object]]]:
    if isinstance(raw, dict):
        workflows = raw.get("workflows")
        if isinstance(workflows, dict):
            return [
                (str(k), v)
                for k, v in workflows.items()
                if isinstance(k, str) and isinstance(v, dict)
            ]
        if isinstance(workflows, list):
            items: list[tuple[str, dict[str, object]]] = []
            for entry in workflows:
                if not isinstance(entry, dict):
                    continue
                entry_id = str(entry.get("id") or uuid.uuid4())
                items.append((entry_id, entry))
            return items
    if isinstance(raw, list):
        items = []
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            entry_id = str(entry.get("id") or uuid.uuid4())
            items.append((entry_id, entry))
        return items
    return []


async def migrate() -> int:
    if not WORKFLOW_FILE.exists():
        return 0

    try:
        raw = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0

    items = _normalize_items(raw)
    migrated = 0
    async with AsyncSessionLocal() as db:
        for workflow_id, payload in items:
            name = str(payload.get("name") or "Untitled Workflow")
            description_obj = payload.get("description")
            description = (
                str(description_obj) if isinstance(description_obj, str) else None
            )
            graph_data_obj = payload.get("graph_data")
            graph_data = (
                graph_data_obj
                if isinstance(graph_data_obj, dict)
                else {"nodes": [], "edges": []}
            )
            template_name_obj = payload.get("template_name")
            template_name = (
                str(template_name_obj)[:200]
                if isinstance(template_name_obj, str) and template_name_obj
                else None
            )

            result = await db.execute(
                select(WorkflowDB).where(WorkflowDB.id == workflow_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(
                    WorkflowDB(
                        id=workflow_id,
                        user_id=str(payload.get("user_id"))
                        if payload.get("user_id") is not None
                        else None,
                        name=name,
                        description=description,
                        graph_data_json=json.dumps(graph_data, ensure_ascii=False),
                        template_name=template_name,
                        created_at=_parse_timestamp(payload.get("created_at")),
                        updated_at=_parse_timestamp(payload.get("updated_at")),
                    )
                )
                migrated += 1
                continue

            existing.name = name
            existing.description = description
            existing.graph_data_json = json.dumps(graph_data, ensure_ascii=False)
            existing.template_name = template_name
            existing.user_id = (
                str(payload.get("user_id"))
                if payload.get("user_id") is not None
                else existing.user_id
            )
            existing.updated_at = _parse_timestamp(payload.get("updated_at"))

        await db.commit()

    return migrated


def main() -> None:
    count = asyncio.run(migrate())
    print(f"migrated_workflows={count}")


if __name__ == "__main__":
    main()
