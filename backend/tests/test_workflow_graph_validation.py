"""
Tests for workflow graph cycle detection.

Validates the WorkflowEngine._has_cycle() DFS coloring algorithm
and the corresponding workflow_error event emission during execute().
"""

from datetime import datetime, timezone

import pytest

from app.core.database import AsyncSessionLocal, init_db
from app.core.workflow.workflow_engine import WorkflowEngine
from app.models.workflow import GraphData, Workflow

from sqlalchemy import text


def _build_workflow(nodes: list, edges: list) -> Workflow:
    now = datetime.now(timezone.utc)
    return Workflow(
        id="wf-cycle-test",
        name="Cycle Test Workflow",
        description=None,
        graph_data=GraphData(nodes=nodes, edges=edges),
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Unit tests: _has_cycle() directly
# ---------------------------------------------------------------------------


class TestHasCycleUnit:
    """Unit tests for the _has_cycle() DFS coloring algorithm."""

    def test_acyclic_graph_passes(self):
        """Linear graph: start -> llm -> end, no cycle."""
        workflow = _build_workflow(
            nodes=[
                {"id": "start-1", "type": "start", "data": {}},
                {"id": "llm-1", "type": "llm", "data": {}},
                {"id": "end-1", "type": "end", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "start-1", "target": "llm-1"},
                {"id": "e2", "source": "llm-1", "target": "end-1"},
            ],
        )
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is False

    def test_simple_cycle_detected(self):
        """A -> B -> A forms a cycle."""
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "start", "data": {}},
                {"id": "B", "type": "llm", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "B"},
                {"id": "e2", "source": "B", "target": "A"},
            ],
        )
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is True

    def test_self_loop_detected(self):
        """A -> A is a self-loop cycle."""
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "llm", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "A"},
            ],
        )
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is True

    def test_complex_cycle_detected(self):
        """A -> B -> C -> A forms a longer cycle."""
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "start", "data": {}},
                {"id": "B", "type": "llm", "data": {}},
                {"id": "C", "type": "llm", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "B"},
                {"id": "e2", "source": "B", "target": "C"},
                {"id": "e3", "source": "C", "target": "A"},
            ],
        )
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is True

    def test_diamond_graph_no_cycle(self):
        """
        Diamond/DAG shape: A -> B, A -> C, B -> D, C -> D.
        Multiple paths to D, but no cycle.
        """
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "start", "data": {}},
                {"id": "B", "type": "llm", "data": {}},
                {"id": "C", "type": "llm", "data": {}},
                {"id": "D", "type": "end", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "B"},
                {"id": "e2", "source": "A", "target": "C"},
                {"id": "e3", "source": "B", "target": "D"},
                {"id": "e4", "source": "C", "target": "D"},
            ],
        )
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is False

    def test_condition_branch_no_false_cycle(self):
        """
        start -> condition -> (true) end
                           -> (false) llm -> end
        Multiple branches but no cycle.
        """
        workflow = _build_workflow(
            nodes=[
                {"id": "start-1", "type": "start", "data": {}},
                {"id": "cond-1", "type": "condition", "data": {"expression": "true"}},
                {"id": "llm-1", "type": "llm", "data": {}},
                {"id": "end-1", "type": "end", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "start-1", "target": "cond-1"},
                {
                    "id": "e2",
                    "source": "cond-1",
                    "target": "end-1",
                    "sourceHandle": "true",
                },
                {
                    "id": "e3",
                    "source": "cond-1",
                    "target": "llm-1",
                    "sourceHandle": "false",
                },
                {"id": "e4", "source": "llm-1", "target": "end-1"},
            ],
        )
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is False

    def test_cycle_in_subgraph_detected(self):
        """
        Main path: start -> end (acyclic).
        Branch: start -> B -> C -> B (cycle in subgraph).
        """
        workflow = _build_workflow(
            nodes=[
                {"id": "start-1", "type": "start", "data": {}},
                {"id": "end-1", "type": "end", "data": {}},
                {"id": "B", "type": "llm", "data": {}},
                {"id": "C", "type": "llm", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "start-1", "target": "end-1"},
                {"id": "e2", "source": "start-1", "target": "B"},
                {"id": "e3", "source": "B", "target": "C"},
                {"id": "e4", "source": "C", "target": "B"},
            ],
        )
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is True

    def test_empty_graph_no_cycle(self):
        """Empty nodes and edges should not crash or report a cycle."""
        workflow = _build_workflow(nodes=[], edges=[])
        engine = WorkflowEngine(workflow)
        assert engine._has_cycle() is False


# ---------------------------------------------------------------------------
# Integration tests: cycle detection through execute()
# ---------------------------------------------------------------------------


class TestCycleDetectionViaExecute:
    """Integration tests verifying cycle detection emits workflow_error events."""

    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """Ensure tables exist before each test, clean up after."""
        await init_db()
        yield
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM workflow_executions"))
            await session.commit()

    @pytest.mark.asyncio
    async def test_simple_cycle_emits_workflow_error(self):
        """A -> B -> A cycle should emit a workflow_error event."""
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "start", "data": {}},
                {"id": "B", "type": "llm", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "B"},
                {"id": "e2", "source": "B", "target": "A"},
            ],
        )
        engine = WorkflowEngine(workflow)
        events = [event async for event in engine.execute("test")]

        error_events = [
            e for e in events if e.get("type") == "workflow_error"
        ]
        assert len(error_events) == 1
        assert "cycle" in error_events[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_self_loop_emits_workflow_error(self):
        """A -> A self-loop should emit a workflow_error event."""
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "start", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "A"},
            ],
        )
        engine = WorkflowEngine(workflow)
        events = [event async for event in engine.execute("test")]

        error_events = [
            e for e in events if e.get("type") == "workflow_error"
        ]
        assert len(error_events) == 1
        assert "cycle" in error_events[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_complex_cycle_emits_workflow_error(self):
        """A -> B -> C -> A should emit a workflow_error event."""
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "start", "data": {}},
                {"id": "B", "type": "llm", "data": {}},
                {"id": "C", "type": "llm", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "B"},
                {"id": "e2", "source": "B", "target": "C"},
                {"id": "e3", "source": "C", "target": "A"},
            ],
        )
        engine = WorkflowEngine(workflow)
        events = [event async for event in engine.execute("test")]

        error_events = [
            e for e in events if e.get("type") == "workflow_error"
        ]
        assert len(error_events) == 1
        assert "cycle" in error_events[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_acyclic_graph_no_workflow_error(self):
        """Linear start -> end graph should complete without workflow_error."""
        workflow = _build_workflow(
            nodes=[
                {"id": "start-1", "type": "start", "data": {}},
                {"id": "end-1", "type": "end", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "start-1", "target": "end-1"},
            ],
        )
        engine = WorkflowEngine(workflow)
        events = [event async for event in engine.execute("test")]

        error_events = [
            e for e in events if e.get("type") == "workflow_error"
        ]
        assert len(error_events) == 0
        assert events[-1]["type"] == "workflow_complete"

    @pytest.mark.asyncio
    async def test_cycle_error_comes_after_workflow_start(self):
        """workflow_start should be emitted before workflow_error for cycles."""
        workflow = _build_workflow(
            nodes=[
                {"id": "A", "type": "start", "data": {}},
                {"id": "B", "type": "llm", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "A", "target": "B"},
                {"id": "e2", "source": "B", "target": "A"},
            ],
        )
        engine = WorkflowEngine(workflow)
        events = [event async for event in engine.execute("test")]

        assert len(events) == 2
        assert events[0]["type"] == "workflow_start"
        assert events[1]["type"] == "workflow_error"
