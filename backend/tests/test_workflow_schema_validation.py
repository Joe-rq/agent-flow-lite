from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api import workflow as workflow_api
from app.models.workflow import GraphData, WorkflowCreate, parse_workflow_nodes


def test_parse_workflow_nodes_accepts_known_types() -> None:
    nodes = [
        {"id": "start-1", "type": "start", "data": {}},
        {"id": "end-1", "type": "end", "data": {}},
    ]

    parsed = parse_workflow_nodes(nodes)

    assert len(parsed) == 2
    assert parsed[0].type == "start"
    assert parsed[1].type == "end"


def test_parse_workflow_nodes_rejects_unknown_types() -> None:
    nodes = [{"id": "x", "type": "__unknown__", "data": {}}]

    with pytest.raises(ValidationError):
        parse_workflow_nodes(nodes)


@pytest.mark.asyncio
async def test_create_workflow_rejects_unknown_node_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(workflow_api, "audit_log", lambda **kwargs: None)

    workflow_data = WorkflowCreate(
        name="bad",
        description=None,
        graph_data=GraphData(
            nodes=[{"id": "x", "type": "__unknown__", "data": {}}], edges=[]
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await workflow_api.create_workflow(
            request=MagicMock(),
            workflow_data=workflow_data,
            user=MagicMock(id=1),
        )

    assert exc.value.status_code == 422
