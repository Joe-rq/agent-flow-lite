import pytest
from fastapi import HTTPException

from app.api import chat as chat_api
from app.models.chat import ChatRequest
from app.models.user import User, UserRole


class StubZep:
    enabled = True

    def ensure_user_session(self, _user_id: str, _session_id: str) -> bool:
        return True

    def add_messages(self, _session_id: str, _messages: list) -> bool:
        return True

    def get_memory_context(self, _session_id: str) -> str:
        return "ZEPCTX"


def create_test_user(user_id: int = 1) -> User:
    """Create a test user."""
    user = User(id=user_id, email=f"user{user_id}@example.com")
    user.role = UserRole.USER
    return user


@pytest.mark.asyncio
async def test_system_prompt_includes_zep_memory(monkeypatch) -> None:
    """Test that Zep memory context is included in system prompt."""
    monkeypatch.setattr(chat_api, "zep_client", lambda: StubZep())
    captured = {}

    def fake_build_system_prompt(has_rag, retrieved_context, memory_context=None):
        captured["memory_context"] = memory_context
        return "prompt"

    monkeypatch.setattr(chat_api, "build_system_prompt", fake_build_system_prompt)

    request = ChatRequest(
        session_id="session-2",
        message="hello",
        user_id="user-1"  # This is now ignored, server-side user_id is used
    )

    user = create_test_user(1)
    response = await chat_api.chat_completions(request, user)
    assert response is not None
    assert captured.get("memory_context") == "ZEPCTX"


@pytest.mark.asyncio
async def test_chat_uses_server_side_user_id(monkeypatch) -> None:
    """Test that server-side user_id is used instead of client-provided user_id."""
    monkeypatch.setattr(chat_api, "zep_client", lambda: StubZep())

    request = ChatRequest(
        session_id="session-1",
        message="hi",
        user_id="client-provided-id"  # Should be ignored
    )

    # Server provides user_id = 42
    user = create_test_user(42)

    # Should not raise, uses server-side user
    response = await chat_api.chat_completions(request, user)
    assert response is not None
    assert response.status_code == 200
