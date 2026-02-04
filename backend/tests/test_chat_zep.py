import pytest
from fastapi import HTTPException

from app.api import chat as chat_api
from app.models.chat import ChatRequest


class StubZep:
    enabled = True

    def ensure_user_session(self, _user_id: str, _session_id: str) -> bool:
        return True

    def add_messages(self, _session_id: str, _messages: list) -> bool:
        return True

    def get_memory_context(self, _session_id: str) -> str:
        return "ZEPCTX"


@pytest.mark.asyncio
async def test_chat_requires_user_id_when_zep_enabled(monkeypatch) -> None:
    monkeypatch.setattr(chat_api, "zep_client", lambda: StubZep())
    request = ChatRequest(session_id="session-1", message="hi")
    with pytest.raises(HTTPException) as exc:
        await chat_api.chat_completions(request)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_system_prompt_includes_zep_memory(monkeypatch) -> None:
    monkeypatch.setattr(chat_api, "zep_client", lambda: StubZep())
    captured = {}

    def fake_build_system_prompt(has_rag, retrieved_context, memory_context=None):
        captured["memory_context"] = memory_context
        return "prompt"

    monkeypatch.setattr(chat_api, "build_system_prompt", fake_build_system_prompt)

    request = ChatRequest(
        session_id="session-2",
        message="hello",
        user_id="user-1"
    )

    response = await chat_api.chat_completions(request)
    assert response is not None
    assert captured.get("memory_context") == "ZEPCTX"
