import json
from datetime import datetime, timezone
import pytest

from app.api import chat_stream as chat_stream_api
from app.core.skill.skill_loader import SkillValidationError
from app.models.chat import ChatRequest, SessionHistory
from app.models.user import User
from app.models.workflow import GraphData, Workflow


def _event_name(chunk: str) -> str:
    for line in chunk.splitlines():
        if line.startswith("event: "):
            return line[7:].strip()
    return ""


def _event_data(chunk: str) -> dict[str, object]:
    for line in chunk.splitlines():
        if line.startswith("data: "):
            payload = line[6:]
            if payload:
                return json.loads(payload)
    return {}


@pytest.mark.asyncio
async def test_chat_stream_generator_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_chat_completion_stream(*args, **kwargs):
        _ = (args, kwargs)
        yield "A"
        yield "B"

    monkeypatch.setattr(
        chat_stream_api, "chat_completion_stream", fake_chat_completion_stream
    )

    request = ChatRequest(session_id="s1", message="hello")
    chunks = [
        chunk
        async for chunk in chat_stream_api.chat_stream_generator(
            request,
            [{"role": "user", "content": "hello"}],
            pre_retrieved_results=[],
            user_id=1,
        )
    ]

    token_payloads = [_event_data(c) for c in chunks if _event_name(c) == "token"]
    done_payloads = [_event_data(c) for c in chunks if _event_name(c) == "done"]

    assert [p.get("content") for p in token_payloads] == ["A", "B"]
    assert done_payloads[-1].get("status") == "success"


@pytest.mark.asyncio
async def test_chat_stream_generator_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_chat_completion_stream(*args, **kwargs):
        _ = (args, kwargs)
        if False:
            yield ""
        raise RuntimeError("boom")

    monkeypatch.setattr(
        chat_stream_api, "chat_completion_stream", fake_chat_completion_stream
    )

    request = ChatRequest(session_id="s1", message="hello")
    chunks = [
        chunk
        async for chunk in chat_stream_api.chat_stream_generator(
            request,
            [{"role": "user", "content": "hello"}],
            pre_retrieved_results=[],
            user_id=1,
        )
    ]

    events = [_event_name(c) for c in chunks]
    assert "error" in events
    assert _event_data(chunks[-1]).get("status") == "error"


@pytest.mark.asyncio
async def test_stream_with_save_accumulates_assistant_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_chat_stream_generator(*args, **kwargs):
        _ = (args, kwargs)
        yield chat_stream_api.format_sse_event("token", {"content": "Hi"})
        yield chat_stream_api.format_sse_event("token", {"content": "!"})
        yield chat_stream_api.format_sse_event("done", {"status": "success"})

    saved_sessions: list[SessionHistory] = []

    async def fake_save_session(session: SessionHistory) -> None:
        saved_sessions.append(session)

    monkeypatch.setattr(
        chat_stream_api, "chat_stream_generator", fake_chat_stream_generator
    )
    monkeypatch.setattr(chat_stream_api, "save_session", fake_save_session)

    session = SessionHistory(session_id="s1")
    request = ChatRequest(session_id="s1", message="hello")

    chunks = [
        chunk
        async for chunk in chat_stream_api.stream_with_save(
            request,
            session,
            [{"role": "user", "content": "hello"}],
            [],
            user_id=1,
        )
    ]

    assert any(_event_name(c) == "done" for c in chunks)
    assert session.messages[-1].content == "Hi!"
    assert len(saved_sessions) == 1


@pytest.mark.asyncio
async def test_workflow_stream_generator_success_saves_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(timezone.utc)
    workflow = Workflow(
        id="wf-1",
        name="wf",
        description=None,
        graph_data=GraphData(),
        created_at=now,
        updated_at=now,
    )

    async def fake_get_workflow(workflow_id: str):
        _ = workflow_id
        return workflow

    class FakeEngine:
        def __init__(self, wf: Workflow):
            self.wf = wf

        async def execute(self, *args, **kwargs):
            _ = (args, kwargs, self.wf)
            yield {"type": "token", "content": "X"}
            yield {"type": "workflow_complete", "final_output": "Done"}

    saved_sessions: list[SessionHistory] = []

    async def fake_save_session(session: SessionHistory) -> None:
        saved_sessions.append(session)

    monkeypatch.setattr(chat_stream_api, "get_workflow", fake_get_workflow)
    monkeypatch.setattr(chat_stream_api, "WorkflowEngine", FakeEngine)
    monkeypatch.setattr(chat_stream_api, "save_session", fake_save_session)

    session = SessionHistory(session_id="s1")
    request = ChatRequest(session_id="s1", message="run", workflow_id="wf-1")
    user = User(id=1, email="wf@example.com")

    chunks = [
        chunk
        async for chunk in chat_stream_api.workflow_stream_generator(
            request,
            session,
            user,
        )
    ]

    assert any(_event_name(c) == "done" for c in chunks)
    assert session.messages[-1].content == "Done"
    assert len(saved_sessions) == 1


@pytest.mark.asyncio
async def test_skill_stream_generator_missing_skill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get_skill(skill_name: str):
        _ = skill_name
        raise SkillValidationError("not found")

    monkeypatch.setattr(chat_stream_api.skill_loader, "get_skill", fake_get_skill)

    session = SessionHistory(session_id="s1")
    user = User(id=1, email="skill@example.com")
    chunks = [
        chunk
        async for chunk in chat_stream_api.skill_stream_generator(
            "unknown-skill",
            "input",
            session,
            user,
        )
    ]

    done_payloads = [_event_data(c) for c in chunks if _event_name(c) == "done"]
    assert done_payloads
    assert done_payloads[-1].get("status") == "error"
