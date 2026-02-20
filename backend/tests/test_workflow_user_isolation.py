"""
Tests for workflow user_id isolation.

Verifies that users can only access their own workflows and legacy
NULL-user_id workflows. Cross-user access must be blocked.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import delete

from app.api import workflow as workflow_api
from app.core.database import AsyncSessionLocal, init_db
from app.models.workflow_db import WorkflowDB


NOW = datetime(2026, 2, 20, tzinfo=timezone.utc)
GRAPH_JSON = json.dumps({"nodes": [], "edges": []})


@pytest.fixture(autouse=True)
async def _setup_db(monkeypatch: pytest.MonkeyPatch) -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        await db.execute(delete(WorkflowDB))
        await db.commit()
    monkeypatch.setattr(workflow_api, "audit_log", lambda **kwargs: None)


async def _insert_workflow(wf_id: str, user_id: str | None) -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            WorkflowDB(
                id=wf_id,
                user_id=user_id,
                name=f"Workflow {wf_id}",
                description=None,
                graph_data_json=GRAPH_JSON,
                created_at=NOW,
                updated_at=NOW,
            )
        )
        await db.commit()


class TestListIsolation:
    @pytest.mark.asyncio
    async def test_user_sees_own_workflows(self) -> None:
        await _insert_workflow("wf-a", "1")
        await _insert_workflow("wf-b", "2")

        result = await workflow_api.list_workflows(user=MagicMock(id=1))
        ids = {w.id for w in result.items}

        assert "wf-a" in ids
        assert "wf-b" not in ids

    @pytest.mark.asyncio
    async def test_user_sees_null_user_id_workflows(self) -> None:
        await _insert_workflow("wf-legacy", None)
        await _insert_workflow("wf-other", "99")

        result = await workflow_api.list_workflows(user=MagicMock(id=1))
        ids = {w.id for w in result.items}

        assert "wf-legacy" in ids
        assert "wf-other" not in ids


class TestGetIsolation:
    @pytest.mark.asyncio
    async def test_owner_can_get(self) -> None:
        await _insert_workflow("wf-mine", "1")

        wf = await workflow_api.get_workflow("wf-mine", user=MagicMock(id=1))
        assert wf.id == "wf-mine"

    @pytest.mark.asyncio
    async def test_other_user_gets_404(self) -> None:
        await _insert_workflow("wf-yours", "2")

        with pytest.raises(HTTPException) as exc:
            await workflow_api.get_workflow("wf-yours", user=MagicMock(id=1))
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_null_user_id_accessible_to_all(self) -> None:
        await _insert_workflow("wf-legacy", None)

        wf = await workflow_api.get_workflow("wf-legacy", user=MagicMock(id=1))
        assert wf.id == "wf-legacy"


class TestDeleteIsolation:
    @pytest.mark.asyncio
    async def test_owner_can_delete(self) -> None:
        await _insert_workflow("wf-mine", "1")

        await workflow_api.delete_workflow(
            request=MagicMock(), workflow_id="wf-mine", user=MagicMock(id=1)
        )

    @pytest.mark.asyncio
    async def test_other_user_cannot_delete(self) -> None:
        await _insert_workflow("wf-yours", "2")

        with pytest.raises(HTTPException) as exc:
            await workflow_api.delete_workflow(
                request=MagicMock(), workflow_id="wf-yours", user=MagicMock(id=1)
            )
        assert exc.value.status_code == 404


class TestExportIsolation:
    @pytest.mark.asyncio
    async def test_owner_can_export(self) -> None:
        await _insert_workflow("wf-mine", "1")

        result = await workflow_api.export_workflow("wf-mine", user=MagicMock(id=1))
        assert result.workflow.name == "Workflow wf-mine"

    @pytest.mark.asyncio
    async def test_other_user_cannot_export(self) -> None:
        await _insert_workflow("wf-yours", "2")

        with pytest.raises(HTTPException) as exc:
            await workflow_api.export_workflow("wf-yours", user=MagicMock(id=1))
        assert exc.value.status_code == 404
