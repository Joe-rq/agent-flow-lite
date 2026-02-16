"""
Authentication tests.

Tests for auth endpoints and token validation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    authenticate_user,
    create_auth_token,
    delete_auth_token,
    get_user_by_token,
    hash_password,
    normalize_email,
    register_user,
    verify_password,
)
from app.core.database import AsyncSessionLocal, engine, init_db
from app.models.user import AuthToken, User, UserRole
from main import create_app


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_session():
    """Provide a database session for tests."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client():
    """Provide a test client."""
    from httpx import AsyncClient, ASGITransport

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup database before each test."""
    await init_db()
    from app.api.auth import _failed_logins, _failed_logins_lock

    with _failed_logins_lock:
        _failed_logins.clear()
    yield
    # Cleanup: Delete all data
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM auth_tokens"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


class TestEmailNormalization:
    """Tests for email normalization."""

    async def test_lowercase_email(self):
        result = normalize_email("User@Example.com")
        assert result == "user@example.com"

    async def test_strip_whitespace(self):
        result = normalize_email("  user@example.com  ")
        assert result == "user@example.com"

    async def test_lowercase_and_strip(self):
        result = normalize_email("  User@EXAMPLE.com  ")
        assert result == "user@example.com"


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    async def test_hash_and_verify(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed)

    async def test_wrong_password_fails(self):
        hashed = hash_password("mypassword")
        assert not verify_password("wrongpassword", hashed)

    async def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"


class TestUserRegistration:
    """Tests for user registration."""

    async def test_register_new_user(self, db_session: AsyncSession):
        user = await register_user(db_session, "test@example.com", "password123")

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password_hash is not None
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.deleted_at is None

    async def test_register_duplicate_email_raises(self, db_session: AsyncSession):
        await register_user(db_session, "test@example.com", "password123")

        with pytest.raises(ValueError, match="already exists"):
            await register_user(db_session, "test@example.com", "password456")

    async def test_admin_role_assigned(self, db_session: AsyncSession):
        from app.core import config

        original = config._settings
        try:
            config._settings = config.Settings(admin_email="admin@test.com")
            user = await register_user(db_session, "admin@test.com", "password123")
            assert user.role == UserRole.ADMIN
        finally:
            config._settings = original

    async def test_no_admin_when_admin_email_empty(self, db_session: AsyncSession):
        from app.core import config

        original = config._settings
        try:
            config._settings = config.Settings(admin_email="")
            user = await register_user(db_session, "anyone@example.com", "password123")
            assert user.role == UserRole.USER
        finally:
            config._settings = original

    async def test_non_admin_role_assigned(self, db_session: AsyncSession):
        user = await register_user(db_session, "regular@example.com", "password123")
        assert user.role == UserRole.USER


class TestUserAuthentication:
    """Tests for user authentication."""

    async def test_authenticate_success(self, db_session: AsyncSession):
        await register_user(db_session, "test@example.com", "password123")
        user = await authenticate_user(db_session, "test@example.com", "password123")

        assert user is not None
        assert user.email == "test@example.com"

    async def test_authenticate_wrong_password(self, db_session: AsyncSession):
        await register_user(db_session, "test@example.com", "password123")
        user = await authenticate_user(db_session, "test@example.com", "wrongpassword")

        assert user is None

    async def test_authenticate_nonexistent_user(self, db_session: AsyncSession):
        user = await authenticate_user(db_session, "noone@example.com", "password123")
        assert user is None


class TestAuthToken:
    """Tests for auth token creation and validation."""

    async def test_create_token(self, db_session: AsyncSession):
        user = await register_user(db_session, "test@example.com", "password123")
        token = await create_auth_token(db_session, user.id)

        assert token.token is not None
        assert len(token.token) == 36  # UUID length
        assert token.user_id == user.id
        assert token.expires_at > datetime.utcnow()

    async def test_get_user_by_valid_token(self, db_session: AsyncSession):
        user = await register_user(db_session, "test@example.com", "password123")
        token = await create_auth_token(db_session, user.id)

        found_user = await get_user_by_token(db_session, token.token)

        assert found_user is not None
        assert found_user.id == user.id

    async def test_get_user_by_invalid_token(self, db_session: AsyncSession):
        found_user = await get_user_by_token(db_session, "invalid-token")
        assert found_user is None

    async def test_expired_token_invalid(self, db_session: AsyncSession):
        user = await register_user(db_session, "test@example.com", "password123")
        token = await create_auth_token(db_session, user.id)

        token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db_session.commit()

        found_user = await get_user_by_token(db_session, token.token)
        assert found_user is None

    async def test_inactive_user_token_returns_user(self, db_session: AsyncSession):
        user = await register_user(db_session, "test@example.com", "password123")
        token = await create_auth_token(db_session, user.id)

        user.is_active = False
        await db_session.commit()

        found_user = await get_user_by_token(db_session, token.token)

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.is_active is False

    async def test_delete_token(self, db_session: AsyncSession):
        user = await register_user(db_session, "test@example.com", "password123")
        token = await create_auth_token(db_session, user.id)

        deleted = await delete_auth_token(db_session, token.token)
        assert deleted is True

        found_user = await get_user_by_token(db_session, token.token)
        assert found_user is None


class TestAuthEndpoints:
    """Tests for auth API endpoints."""

    async def test_register_creates_user(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert len(data["token"]) == 36

    async def test_register_duplicate_email(self, client):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password456"},
        )
        assert response.status_code == 409

    async def test_register_short_password(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "12345"},
        )
        assert response.status_code == 400

    async def test_register_empty_password(self, client):
        response = await client.post(
            "/api/v1/auth/register", json={"email": "test@example.com", "password": ""}
        )
        assert response.status_code == 400

    async def test_login_success(self, client):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == "test@example.com"

    async def test_login_wrong_password(self, client):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "noone@example.com", "password": "password123"},
        )
        assert response.status_code == 401

    async def test_login_rate_limited_after_repeated_failures(self, client):
        email = "lock@example.com"
        await client.post(
            "/api/v1/auth/register", json={"email": email, "password": "password123"}
        )

        for _ in range(5):
            response = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": "wrongpassword"}
            )
            assert response.status_code == 401

        blocked = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "password123"}
        )
        assert blocked.status_code == 429
        assert blocked.headers.get("Retry-After") is not None

    async def test_login_invalid_email(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "invalid-email", "password": "password123"},
        )
        assert response.status_code == 400

    async def test_login_rejects_bare_at(self, client):
        response = await client.post(
            "/api/v1/auth/login", json={"email": "@", "password": "password123"}
        )
        assert response.status_code == 400

    async def test_login_rejects_double_at(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@@domain.com", "password": "password123"},
        )
        assert response.status_code == 400

    async def test_login_rejects_no_tld(self, client):
        response = await client.post(
            "/api/v1/auth/login", json={"email": "a@b", "password": "password123"}
        )
        assert response.status_code == 400

    async def test_login_rejects_empty_email(self, client):
        response = await client.post(
            "/api/v1/auth/login", json={"email": "", "password": "password123"}
        )
        assert response.status_code == 400

    async def test_login_rejects_empty_password(self, client):
        response = await client.post(
            "/api/v1/auth/login", json={"email": "test@example.com", "password": ""}
        )
        assert response.status_code == 400

    async def test_me_endpoint(self, client):
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = reg.json()["token"]

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    async def test_me_without_token(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_with_invalid_token(self, client):
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    async def test_logout_endpoint(self, client):
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = reg.json()["token"]

        response = await client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        me_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 401

    async def test_logout_without_token(self, client):
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    async def test_disabled_user_cannot_access(self, client):
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = reg.json()["token"]
        user_id = reg.json()["user"]["id"]

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one()
            user.is_active = False
            await session.commit()

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    async def test_disabled_user_cannot_login(self, client):
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = reg.json()["user"]["id"]

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one()
            user.is_active = False
            await session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 403
