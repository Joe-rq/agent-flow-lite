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


@pytest.mark.asyncio
@pytest.mark.parametrize('expression', ['true', 'false'])
async def test_condition_edge_without_source_handle_is_compatible(expression: str) -> None:
    workflow = build_workflow(
        GraphData(
            nodes=[
                {'id': 'start-1', 'type': 'start', 'data': {}},
                {'id': 'cond-1', 'type': 'condition', 'data': {'expression': expression}},
                {'id': 'end-1', 'type': 'end', 'data': {}},
            ],
            edges=[
                {'id': 'e-start-cond', 'source': 'start-1', 'target': 'cond-1'},
                {'id': 'e-cond-end', 'source': 'cond-1', 'target': 'end-1'},
            ],
        )
    )

    engine = WorkflowEngine(workflow)

    events = [event async for event in engine.execute('payload')]

    assert any(e.get('type') == 'node_complete' and e.get('node_id') == 'end-1' for e in events)
    assert events[-1]['type'] == 'workflow_complete'
    assert events[-1]['final_output'] == 'payload'
