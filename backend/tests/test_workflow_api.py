from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import delete

from app.api import workflow as workflow_api
from app.core.database import AsyncSessionLocal, init_db
from app.models.workflow_db import WorkflowDB


@pytest.mark.asyncio
async def test_list_workflows_handles_mixed_datetime_offsets() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        await db.execute(delete(WorkflowDB))
        db.add_all(
            [
                WorkflowDB(
                    id="wf-aware",
                    name="Aware Workflow",
                    description=None,
                    graph_data_json='{"nodes": [], "edges": []}',
                    created_at=datetime(2026, 2, 7, 10, 0, 0, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 2, 7, 10, 0, 0, tzinfo=timezone.utc),
                ),
                WorkflowDB(
                    id="wf-naive",
                    name="Naive Workflow",
                    description=None,
                    graph_data_json='{"nodes": [], "edges": []}',
                    created_at=datetime(2026, 2, 8, 9, 0, 0),
                    updated_at=datetime(2026, 2, 8, 9, 0, 0),
                ),
            ]
        )
        await db.commit()

    result = await workflow_api.list_workflows(user=MagicMock())

    assert result.total == 2
    assert [item.id for item in result.items] == ["wf-naive", "wf-aware"]
    assert all(item.created_at.tzinfo is not None for item in result.items)
