import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from filelock import FileLock

from app.api import workflow as workflow_api
from app.models.workflow import GraphData


def _write_workflows(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@pytest.fixture()
def isolated_workflow_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "data"
    workflow_file = data_dir / "workflows.json"
    lock = FileLock(str(workflow_file) + ".lock")

    monkeypatch.setattr(workflow_api, "DATA_DIR", data_dir)
    monkeypatch.setattr(workflow_api, "WORKFLOW_FILE", workflow_file)
    monkeypatch.setattr(workflow_api, "_workflow_lock", lock)
    monkeypatch.setattr(workflow_api, "audit_log", lambda **kwargs: None)

    return workflow_file


@pytest.mark.asyncio
async def test_export_then_import_roundtrip_creates_new_workflow_id(
    isolated_workflow_store: Path,
) -> None:
    original_id = "wf-orig"
    now = "2026-02-01T00:00:00+00:00"
    graph = {
        "nodes": [
            {"id": "start-1", "type": "start", "data": {}},
            {"id": "end-1", "type": "end", "data": {}},
        ],
        "edges": [],
    }
    _write_workflows(
        isolated_workflow_store,
        {
            "workflows": {
                original_id: {
                    "name": "Demo",
                    "description": "Roundtrip",
                    "graph_data": graph,
                    "created_at": now,
                    "updated_at": now,
                }
            }
        },
    )

    exported = await workflow_api.export_workflow(
        workflow_id=original_id,
        user=MagicMock(),
    )
    assert exported.version == workflow_api.EXPORT_VERSION
    assert exported.workflow.name == "Demo"
    assert exported.workflow.description == "Roundtrip"

    imported = await workflow_api.import_workflow(
        request=MagicMock(),
        payload=workflow_api.WorkflowImportPayload(**exported.model_dump()),
        user=MagicMock(id=1),
    )

    assert imported.id != original_id
    assert imported.name == "Demo"
    assert imported.description == "Roundtrip"
    assert imported.graph_data.model_dump() == graph

    with open(isolated_workflow_store, "r", encoding="utf-8") as f:
        stored = json.load(f)
    assert original_id in stored.get("workflows", {})
    assert imported.id in stored.get("workflows", {})


@pytest.mark.asyncio
async def test_import_rejects_unknown_node_type_with_4xx(
    isolated_workflow_store: Path,
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

    with pytest.raises(HTTPException) as exc:
        await workflow_api.import_workflow(
            request=MagicMock(),
            payload=payload,
            user=MagicMock(id=1),
        )

    assert 400 <= exc.value.status_code < 500


@pytest.mark.asyncio
async def test_import_is_atomic_on_write_failure(
    isolated_workflow_store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = "2026-02-01T00:00:00+00:00"
    _write_workflows(
        isolated_workflow_store,
        {
            "workflows": {
                "wf-existing": {
                    "name": "Existing",
                    "description": None,
                    "graph_data": {"nodes": [], "edges": []},
                    "created_at": now,
                    "updated_at": now,
                }
            }
        },
    )

    before_bytes = isolated_workflow_store.read_bytes()

    def _boom_replace(src, dst) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(workflow_api.os, "replace", _boom_replace)

    payload = workflow_api.WorkflowImportPayload(
        version=workflow_api.EXPORT_VERSION,
        workflow=workflow_api.WorkflowExportObject(
            name="Imported",
            description="x",
            graph_data=GraphData(
                nodes=[{"id": "start-1", "type": "start", "data": {}}],
                edges=[],
            ),
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await workflow_api.import_workflow(
            request=MagicMock(),
            payload=payload,
            user=MagicMock(id=1),
        )

    assert exc.value.status_code == 500
    assert isolated_workflow_store.read_bytes() == before_bytes
