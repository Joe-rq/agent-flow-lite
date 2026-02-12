from datetime import datetime, timezone

import pytest

from app.core.workflow.workflow_engine import WorkflowEngine
from app.models.workflow import GraphData, Workflow


def build_workflow(graph_data: GraphData) -> Workflow:
    now = datetime.now(timezone.utc)
    return Workflow(
        id='wf-test',
        name='Test Workflow',
        description=None,
        graph_data=graph_data,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_engine_uses_graph_data_model() -> None:
    workflow = build_workflow(
        GraphData(
            nodes=[{'id': 'start-1', 'type': 'start', 'data': {}}],
            edges=[],
        )
    )

    engine = WorkflowEngine(workflow)

    events = [event async for event in engine.execute('hello')]

    assert events[0]['type'] == 'workflow_start'
    assert events[-1]['type'] == 'workflow_complete'
