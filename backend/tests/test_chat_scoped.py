"""
Tests for user-scoped chat sessions.

These tests verify that:
1. Sessions are isolated by user (users can only access their own sessions)
2. Admins can access all sessions
3. Client-provided user_id is ignored (server-side user_id is used)
"""

import pytest
import pytest_asyncio
from datetime import datetime
from fastapi import HTTPException

from app.api import chat as chat_api
from app.api.chat_session import (
    check_session_ownership,
    save_session,
    load_session,
    delete_session_by_id,
)
from app.models.user import User, UserRole
from app.models.chat import ChatRequest, SessionHistory, ChatMessage


class TestUser:
    """Test user factory."""

    @staticmethod
    def regular(user_id: int = 123) -> User:
        """Create a regular test user."""
        user = User(id=user_id, email=f"user{user_id}@example.com")
        user.role = UserRole.USER
        return user

    @staticmethod
    def admin(user_id: int = 999) -> User:
        """Create an admin test user."""
        user = User(id=user_id, email=f"admin{user_id}@example.com")
        user.role = UserRole.ADMIN
        return user


@pytest_asyncio.fixture
async def cleanup_sessions():
    """Cleanup test sessions after each test."""
    test_session_ids = []
    yield test_session_ids
    # Cleanup
    for session_id in test_session_ids:
        _ = await delete_session_by_id(session_id)


class TestCheckSessionOwnership:
    """Tests for check_session_ownership function."""

    def test_owner_can_access_own_session(self):
        session = SessionHistory(session_id="test-session", user_id="123")
        user = TestUser.regular(123)
        assert check_session_ownership(session, user) is True

    def test_other_user_cannot_access_session(self):
        session = SessionHistory(session_id="test-session", user_id="123")
        user = TestUser.regular(456)
        assert check_session_ownership(session, user) is False

    def test_admin_can_access_any_session(self):
        session = SessionHistory(session_id="test-session", user_id="123")
        admin = TestUser.admin(999)
        assert check_session_ownership(session, admin) is True

    def test_orphaned_session_accessible_to_all(self):
        """Sessions without user_id are treated as orphaned (backward compatibility)."""
        session = SessionHistory(session_id="test-session", user_id=None)
        user = TestUser.regular(123)
        assert check_session_ownership(session, user) is True


class TestListSessions:
    """Tests for list_sessions endpoint."""

    @pytest.mark.asyncio
    async def test_user_sees_only_own_sessions(self, cleanup_sessions):
        # Create sessions for two users
        session1 = SessionHistory(
            session_id="session-user1-1",
            user_id="1",
            messages=[
                ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow())
            ],
        )
        session2 = SessionHistory(
            session_id="session-user1-2",
            user_id="1",
            messages=[
                ChatMessage(role="user", content="World", timestamp=datetime.utcnow())
            ],
        )
        session3 = SessionHistory(
            session_id="session-user2-1",
            user_id="2",
            messages=[
                ChatMessage(role="user", content="Other", timestamp=datetime.utcnow())
            ],
        )

        await save_session(session1)
        await save_session(session2)
        await save_session(session3)
        cleanup_sessions.extend(
            ["session-user1-1", "session-user1-2", "session-user2-1"]
        )

        user = TestUser.regular(1)
        result = await chat_api.list_sessions(user)

        session_ids = [s["session_id"] for s in result["sessions"]]
        assert "session-user1-1" in session_ids
        assert "session-user1-2" in session_ids
        assert "session-user2-1" not in session_ids

    @pytest.mark.asyncio
    async def test_admin_sees_all_sessions(self, cleanup_sessions):
        # Create sessions for different users
        session1 = SessionHistory(
            session_id="session-admin-test-1",
            user_id="1",
            messages=[
                ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow())
            ],
        )
        session2 = SessionHistory(
            session_id="session-admin-test-2",
            user_id="2",
            messages=[
                ChatMessage(role="user", content="World", timestamp=datetime.utcnow())
            ],
        )

        await save_session(session1)
        await save_session(session2)
        cleanup_sessions.extend(["session-admin-test-1", "session-admin-test-2"])

        admin = TestUser.admin(999)
        result = await chat_api.list_sessions(admin)

        session_ids = [s["session_id"] for s in result["sessions"]]
        assert "session-admin-test-1" in session_ids
        assert "session-admin-test-2" in session_ids

    @pytest.mark.asyncio
    async def test_orphaned_sessions_visible_to_all(self, cleanup_sessions):
        """Sessions without user_id are visible to all users (backward compatibility)."""
        session = SessionHistory(
            session_id="orphan-session",
            user_id=None,
            messages=[
                ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow())
            ],
        )
        await save_session(session)
        cleanup_sessions.append("orphan-session")

        user = TestUser.regular(123)
        result = await chat_api.list_sessions(user)

        session_ids = [s["session_id"] for s in result["sessions"]]
        assert "orphan-session" in session_ids


class TestGetSessionHistory:
    """Tests for get_session_history endpoint."""

    @pytest.mark.asyncio
    async def test_owner_can_get_session(self, cleanup_sessions):
        session = SessionHistory(
            session_id="owner-test-session",
            user_id="123",
            messages=[
                ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow())
            ],
        )
        await save_session(session)
        cleanup_sessions.append("owner-test-session")

        user = TestUser.regular(123)
        result = await chat_api.get_session_history("owner-test-session", user)

        assert result["session_id"] == "owner-test-session"

    @pytest.mark.asyncio
    async def test_non_owner_cannot_get_session(self, cleanup_sessions):
        session = SessionHistory(
            session_id="private-session",
            user_id="123",
            messages=[
                ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow())
            ],
        )
        await save_session(session)
        cleanup_sessions.append("private-session")

        user = TestUser.regular(456)
        with pytest.raises(HTTPException) as exc:
            await chat_api.get_session_history("private-session", user)

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_get_any_session(self, cleanup_sessions):
        session = SessionHistory(
            session_id="admin-access-session",
            user_id="123",
            messages=[
                ChatMessage(role="user", content="Hello", timestamp=datetime.utcnow())
            ],
        )
        await save_session(session)
        cleanup_sessions.append("admin-access-session")

        admin = TestUser.admin(999)
        result = await chat_api.get_session_history("admin-access-session", admin)

        assert result["session_id"] == "admin-access-session"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_returns_404(self):
        user = TestUser.regular(123)
        with pytest.raises(HTTPException) as exc:
            await chat_api.get_session_history("nonexistent-session", user)

        assert exc.value.status_code == 404


class TestDeleteSession:
    """Tests for delete_session endpoint."""

    @pytest.mark.asyncio
    async def test_owner_can_delete_session(self, cleanup_sessions):
        session = SessionHistory(
            session_id="delete-own-session", user_id="123", messages=[]
        )
        await save_session(session)
        cleanup_sessions.append("delete-own-session")

        user = TestUser.regular(123)
        result = await chat_api.delete_session("delete-own-session", user)

        assert result["status"] == "success"
        # Verify session is deleted
        assert await load_session("delete-own-session") is None

    @pytest.mark.asyncio
    async def test_non_owner_cannot_delete_session(self, cleanup_sessions):
        session = SessionHistory(
            session_id="protected-session", user_id="123", messages=[]
        )
        await save_session(session)
        cleanup_sessions.append("protected-session")

        user = TestUser.regular(456)
        with pytest.raises(HTTPException) as exc:
            await chat_api.delete_session("protected-session", user)

        assert exc.value.status_code == 403
        # Verify session still exists
        assert await load_session("protected-session") is not None

    @pytest.mark.asyncio
    async def test_admin_can_delete_any_session(self, cleanup_sessions):
        session = SessionHistory(
            session_id="admin-delete-session", user_id="123", messages=[]
        )
        await save_session(session)
        cleanup_sessions.append("admin-delete-session")

        admin = TestUser.admin(999)
        result = await chat_api.delete_session("admin-delete-session", admin)

        assert result["status"] == "success"
        assert await load_session("admin-delete-session") is None


class TestChatCompletionsUserId:
    """Tests that chat_completions uses server-side user_id correctly."""

    @pytest.mark.asyncio
    async def test_ignores_client_provided_user_id(self, cleanup_sessions):
        """Client-provided user_id should be ignored; server-side user_id should be used."""
        request = ChatRequest(
            session_id="test-session-user-id",
            message="Hello",
            user_id="client-provided-user-id",  # This should be ignored
        )
        user = TestUser.regular(999)  # server-side user_id = 999

        response = await chat_api.chat_completions(request, user)
        assert response is not None
        assert response.status_code == 200
        cleanup_sessions.append("test-session-user-id")

    @pytest.mark.asyncio
    async def test_session_ownership_checked_in_completions(self, cleanup_sessions):
        """User should not be able to access another user's existing session."""
        # Create a session owned by another user
        existing_session = SessionHistory(
            session_id="owned-session", user_id="123", messages=[]
        )
        await save_session(existing_session)
        cleanup_sessions.append("owned-session")

        request = ChatRequest(session_id="owned-session", message="Hello")
        attacker = TestUser.regular(456)

        with pytest.raises(HTTPException) as exc:
            await chat_api.chat_completions(request, attacker)

        assert exc.value.status_code == 403
