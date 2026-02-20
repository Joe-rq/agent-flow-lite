import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

from app.api import workflow as workflow_api
from app.core.database import AsyncSessionLocal, init_db
from app.models.workflow import GraphData
from app.models.workflow_db import WorkflowDB


@pytest.fixture()
async def isolated_workflow_store(monkeypatch: pytest.MonkeyPatch) -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        await db.execute(delete(WorkflowDB))
        await db.commit()
    monkeypatch.setattr(workflow_api, "audit_log", lambda **kwargs: None)


@pytest.mark.asyncio
async def test_export_then_import_roundtrip_creates_new_workflow_id(
    isolated_workflow_store: None,
) -> None:
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    graph = {
        "nodes": [
            {"id": "start-1", "type": "start", "data": {}},
            {"id": "end-1", "type": "end", "data": {}},
        ],
        "edges": [],
    }

    async with AsyncSessionLocal() as db:
        db.add(
            WorkflowDB(
                id="wf-orig",
                user_id="1",
                name="Demo",
                description="Roundtrip",
                graph_data_json=json.dumps(graph, ensure_ascii=False),
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()

    exported = await workflow_api.export_workflow(
        workflow_id="wf-orig",
        user=MagicMock(id=1),
    )
    assert exported.version == workflow_api.EXPORT_VERSION
    assert exported.workflow.name == "Demo"
    assert exported.workflow.description == "Roundtrip"

    request = MagicMock()
    request.headers = {}
    imported = await workflow_api.import_workflow(
        request=request,
        payload=workflow_api.WorkflowImportPayload(**exported.model_dump()),
        user=MagicMock(id=1),
    )

    assert imported.id != "wf-orig"
    assert imported.name == "Demo"
    assert imported.description == "Roundtrip"
    assert imported.graph_data.model_dump() == graph

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WorkflowDB.id))
        ids = {row[0] for row in result.all()}
    assert "wf-orig" in ids
    assert imported.id in ids


@pytest.mark.asyncio
async def test_import_rejects_unknown_node_type_with_4xx(
    isolated_workflow_store: None,
) -> None:
    payload = workflow_api.WorkflowImportPayload(
        version=workflow_api.EXPORT_VERSION,
        workflow=workflow_api.WorkflowExportObject(
            name="Bad",
            description=None,
            graph_data=GraphData(
                nodes=[{"id": "x", "type": "__unknown__", "data": {}}],
                edges=[],
            ),
        ),
    )

    request = MagicMock()
    request.headers = {}
    with pytest.raises(HTTPException) as exc:
        await workflow_api.import_workflow(
            request=request,
            payload=payload,
            user=MagicMock(id=1),
        )

    assert 400 <= exc.value.status_code < 500


@pytest.mark.asyncio
async def test_import_validation_failure_keeps_existing_data(
    isolated_workflow_store: None,
) -> None:
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    async with AsyncSessionLocal() as db:
        db.add(
            WorkflowDB(
                id="wf-existing",
                user_id="1",
                name="Existing",
                description=None,
                graph_data_json=json.dumps(
                    {"nodes": [], "edges": []}, ensure_ascii=False
                ),
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()

    bad_payload = workflow_api.WorkflowImportPayload(
        version=workflow_api.EXPORT_VERSION,
        workflow=workflow_api.WorkflowExportObject(
            name="Imported",
            description="x",
            graph_data=GraphData(
                nodes=[{"id": "x", "type": "__unknown__", "data": {}}],
                edges=[],
            ),
        ),
    )

    request = MagicMock()
    request.headers = {}
    with pytest.raises(HTTPException):
        await workflow_api.import_workflow(
            request=request,
            payload=bad_payload,
            user=MagicMock(id=1),
        )

    async with AsyncSessionLocal() as db:
        count = await db.execute(select(WorkflowDB))
        rows = count.scalars().all()
    assert len(rows) == 1
    assert rows[0].id == "wf-existing"
