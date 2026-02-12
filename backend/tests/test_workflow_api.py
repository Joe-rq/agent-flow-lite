"""Tests for workflow API helpers and endpoints."""
from unittest.mock import MagicMock

import pytest

from app.api import workflow as workflow_api


@pytest.mark.asyncio
async def test_list_workflows_handles_mixed_datetime_offsets(monkeypatch: pytest.MonkeyPatch) -> None:
    """List endpoint should sort safely when stored timestamps mix naive/aware formats."""
    mock_data = {
        'workflows': {
            'wf-aware': {
                'name': 'Aware Workflow',
                'description': None,
                'graph_data': {'nodes': [], 'edges': []},
                'created_at': '2026-02-07T10:00:00+00:00',
                'updated_at': '2026-02-07T10:00:00+00:00',
            },
            'wf-naive': {
                'name': 'Naive Workflow',
                'description': None,
                'graph_data': {'nodes': [], 'edges': []},
                'created_at': '2026-02-08T09:00:00',
                'updated_at': '2026-02-08T09:00:00',
            },
        }
    }

    monkeypatch.setattr(workflow_api, 'load_workflows_readonly', lambda: mock_data)

    result = await workflow_api.list_workflows(user=MagicMock())

    assert result.total == 2
    assert [item.id for item in result.items] == ['wf-naive', 'wf-aware']
    assert all(item.created_at.tzinfo is not None for item in result.items)
