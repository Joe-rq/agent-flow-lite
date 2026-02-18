"""
Tests for workflow execution persistence and resume capability.
"""

import json
from collections import deque
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, init_db
from app.core.workflow.workflow_context import ExecutionContext
from app.core.workflow.workflow_engine import WorkflowEngine
from app.models.workflow import GraphData, Workflow
from app.models.workflow_execution_db import WorkflowExecutionDB


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Ensure tables exist before each test, clean up after."""
    await init_db()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM workflow_executions"))
        await session.execute(text("DELETE FROM workflows"))
        await session.commit()


def _build_workflow(graph_data: GraphData, workflow_id: str = "wf-test") -> Workflow:
    now = datetime.now(timezone.utc)
    return Workflow(
        id=workflow_id,
        name="Test Workflow",
        description=None,
        graph_data=graph_data,
        created_at=now,
        updated_at=now,
    )


class TestCheckpointSerialization:
    """Test checkpoint serialization/deserialization roundtrip."""

    def test_to_checkpoint_returns_dict(self):
        ctx = ExecutionContext("hello", user_id=1, model="test-model")
        ctx.set_output("node-1", "result-1")
        ctx.set_output("node-2", {"key": "value"})

        checkpoint = ctx.to_checkpoint()

        assert isinstance(checkpoint, dict)
        assert "step_outputs" in checkpoint
        assert "variables" in checkpoint
        assert "conversation_history" in checkpoint
        assert checkpoint["step_outputs"]["node-1"] == "result-1"
        assert checkpoint["step_outputs"]["node-2"] == {"key": "value"}
        assert checkpoint["variables"]["input"] == "hello"
        assert checkpoint["variables"]["node-1.output"] == "result-1"

    def test_from_checkpoint_restores_state(self):
        original = ExecutionContext("hello", user_id=1, model="test-model")
        original.set_output("node-1", "result-1")
        original.set_output("node-2", {"key": "value"})
        original.conversation_history = [{"role": "user", "content": "hi"}]

        checkpoint = original.to_checkpoint()
        restored = ExecutionContext.from_checkpoint(
            checkpoint, initial_input="hello", user_id=1, model="test-model"
        )

        assert restored.step_outputs == original.step_outputs
        assert restored.variables == original.variables
        assert restored.conversation_history == original.conversation_history
        assert restored.user_id == 1
        assert restored.model == "test-model"

    def test_checkpoint_is_json_serializable(self):
        ctx = ExecutionContext("test input")
        ctx.set_output("n1", "output text")
        ctx.set_output("n2", 42)
        ctx.set_output("n3", ["a", "b", "c"])

        checkpoint = ctx.to_checkpoint()
        serialized = json.dumps(checkpoint)
        deserialized = json.loads(serialized)

        restored = ExecutionContext.from_checkpoint(
            deserialized, initial_input="test input"
        )
        assert restored.step_outputs == ctx.step_outputs

    def test_from_checkpoint_with_empty_data(self):
        restored = ExecutionContext.from_checkpoint(
            {}, initial_input="hello"
        )

        assert restored.variables == {"input": "hello"}
        assert restored.step_outputs == {}
        assert restored.conversation_history == []


class TestExecutionCreatesDBRecord:
    """Test that workflow execution creates and updates DB records."""

    async def test_execute_creates_record(self):
        workflow = _build_workflow(
            GraphData(
                nodes=[{"id": "start-1", "type": "start", "data": {}}],
                edges=[],
            )
        )
        engine = WorkflowEngine(workflow)
        execution_id = "test-exec-001"

        events = []
        async for event in engine.execute(
            "hello", execution_id=execution_id
        ):
            events.append(event)

        assert events[0]["type"] == "workflow_start"
        assert events[0]["execution_id"] == execution_id
        assert events[-1]["type"] == "workflow_complete"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowExecutionDB).where(
                    WorkflowExecutionDB.id == execution_id
                )
            )
            row = result.scalar_one_or_none()

        assert row is not None
        assert row.workflow_id == "wf-test"
        assert row.status == "completed"
        assert row.initial_input == "hello"

    async def test_execution_id_auto_generated(self):
        workflow = _build_workflow(
            GraphData(
                nodes=[{"id": "start-1", "type": "start", "data": {}}],
                edges=[],
            )
        )
        engine = WorkflowEngine(workflow)

        events = [event async for event in engine.execute("hello")]

        execution_id = events[0].get("execution_id")
        assert execution_id is not None
        assert len(execution_id) == 36  # UUID length


class TestStatusTransitions:
    """Test status transitions: running -> completed, running -> failed."""

    async def test_successful_execution_completes(self):
        workflow = _build_workflow(
            GraphData(
                nodes=[{"id": "start-1", "type": "start", "data": {}}],
                edges=[],
            )
        )
        engine = WorkflowEngine(workflow)
        execution_id = "test-status-ok"

        events = [
            event
            async for event in engine.execute("hi", execution_id=execution_id)
        ]

        assert events[-1]["type"] == "workflow_complete"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowExecutionDB).where(
                    WorkflowExecutionDB.id == execution_id
                )
            )
            row = result.scalar_one()

        assert row.status == "completed"

    async def test_no_start_node_does_not_create_record(self):
        workflow = _build_workflow(
            GraphData(
                nodes=[{"id": "end-1", "type": "end", "data": {}}],
                edges=[],
            )
        )
        engine = WorkflowEngine(workflow)
        execution_id = "test-no-start"

        events = [
            event
            async for event in engine.execute("hi", execution_id=execution_id)
        ]

        assert any(e["type"] == "workflow_error" for e in events)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowExecutionDB).where(
                    WorkflowExecutionDB.id == execution_id
                )
            )
            row = result.scalar_one_or_none()

        assert row is None


class TestCheckpointPersistence:
    """Test that checkpoints are saved to the database after each node."""

    async def test_checkpoint_saved_after_node_execution(self):
        workflow = _build_workflow(
            GraphData(
                nodes=[
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                edges=[
                    {
                        "id": "e-start-end",
                        "source": "start-1",
                        "target": "end-1",
                    }
                ],
            )
        )
        engine = WorkflowEngine(workflow)
        execution_id = "test-checkpoint"

        events = [
            event
            async for event in engine.execute("hi", execution_id=execution_id)
        ]

        assert events[-1]["type"] == "workflow_complete"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowExecutionDB).where(
                    WorkflowExecutionDB.id == execution_id
                )
            )
            row = result.scalar_one()

        executed_nodes = json.loads(row.executed_nodes_json)
        assert "start-1" in executed_nodes
        assert row.status == "completed"


class TestResumeExecution:
    """Test resuming a checkpointed execution."""

    async def test_resume_nonexistent_execution(self):
        events = [
            event async for event in WorkflowEngine.resume("nonexistent-id")
        ]
        assert any(
            e.get("type") == "workflow_error"
            and "not found" in e.get("error", "")
            for e in events
        )

    async def test_resume_completed_execution_errors(self):
        workflow = _build_workflow(
            GraphData(
                nodes=[{"id": "start-1", "type": "start", "data": {}}],
                edges=[],
            )
        )
        engine = WorkflowEngine(workflow)
        execution_id = "test-resume-completed"

        events = [
            event
            async for event in engine.execute("hi", execution_id=execution_id)
        ]
        assert events[-1]["type"] == "workflow_complete"

        resume_events = [
            event async for event in WorkflowEngine.resume(execution_id)
        ]
        assert any(
            e.get("type") == "workflow_error"
            and "already completed" in e.get("error", "")
            for e in resume_events
        )
