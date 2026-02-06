"""
Authentication tests.

Tests for auth endpoints and token validation.
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_auth_token,
    delete_auth_token,
    get_or_create_user,
    get_user_by_token,
    normalize_email,
)
from app.core.database import AsyncSessionLocal, engine, init_db
from app.core.config import settings
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
        # Cleanup after test
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
    yield
    # Cleanup: Delete all data
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM auth_tokens"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


class TestEmailNormalization:
    """Tests for email normalization."""
    
    async def test_lowercase_email(self):
        """Test email is converted to lowercase."""
        result = await normalize_email("User@Example.com")
        assert result == "user@example.com"
    
    async def test_strip_whitespace(self):
        """Test whitespace is stripped from email."""
        result = await normalize_email("  user@example.com  ")
        assert result == "user@example.com"
    
    async def test_lowercase_and_strip(self):
        """Test both lowercase and whitespace stripping."""
        result = await normalize_email("  User@EXAMPLE.com  ")
        assert result == "user@example.com"


class TestUserCreation:
    """Tests for user creation and retrieval."""
    
    async def test_create_new_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        user = await get_or_create_user(db_session, "test@example.com")
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.deleted_at is None
    
    async def test_get_existing_user(self, db_session: AsyncSession):
        """Test getting existing user doesn't create duplicate."""
        # Create user first
        user1 = await get_or_create_user(db_session, "test@example.com")
        
        # Get same user again
        user2 = await get_or_create_user(db_session, "test@example.com")
        
        assert user1.id == user2.id
    
    async def test_admin_role_assigned(self, db_session: AsyncSession):
        """Test admin role is assigned for admin email."""
        admin_email = settings().admin_email
        user = await get_or_create_user(db_session, admin_email)
        
        assert user.role == UserRole.ADMIN
    
    async def test_non_admin_role_assigned(self, db_session: AsyncSession):
        """Test user role is assigned for non-admin email."""
        user = await get_or_create_user(db_session, "regular@example.com")
        
        assert user.role == UserRole.USER


class TestAuthToken:
    """Tests for auth token creation and validation."""
    
    async def test_create_token(self, db_session: AsyncSession):
        """Test creating an auth token."""
        user = await get_or_create_user(db_session, "test@example.com")
        token = await create_auth_token(db_session, user.id)
        
        assert token.token is not None
        assert len(token.token) == 36  # UUID length
        assert token.user_id == user.id
        # Compare with naive datetime since SQLite doesn't store timezone
        assert token.expires_at > datetime.utcnow()
    
    async def test_get_user_by_valid_token(self, db_session: AsyncSession):
        """Test getting user by valid token."""
        user = await get_or_create_user(db_session, "test@example.com")
        token = await create_auth_token(db_session, user.id)
        
        found_user = await get_user_by_token(db_session, token.token)
        
        assert found_user is not None
        assert found_user.id == user.id
    
    async def test_get_user_by_invalid_token(self, db_session: AsyncSession):
        """Test getting user by invalid token returns None."""
        found_user = await get_user_by_token(db_session, "invalid-token")
        
        assert found_user is None
    
    async def test_expired_token_invalid(self, db_session: AsyncSession):
        """Test expired token is invalid."""
        user = await get_or_create_user(db_session, "test@example.com")
        token = await create_auth_token(db_session, user.id)
        
        # Manually expire the token
        token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db_session.commit()
        
        found_user = await get_user_by_token(db_session, token.token)
        
        assert found_user is None
    
    async def test_inactive_user_token_returns_user(self, db_session: AsyncSession):
        """Test token for inactive user returns user (is_active check done separately)."""
        user = await get_or_create_user(db_session, "test@example.com")
        token = await create_auth_token(db_session, user.id)

        # Deactivate user
        user.is_active = False
        await db_session.commit()

        # get_user_by_token now returns user even if inactive (for 403 handling)
        found_user = await get_user_by_token(db_session, token.token)

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.is_active is False
    
    async def test_delete_token(self, db_session: AsyncSession):
        """Test deleting a token."""
        user = await get_or_create_user(db_session, "test@example.com")
        token = await create_auth_token(db_session, user.id)
        
        deleted = await delete_auth_token(db_session, token.token)
        
        assert deleted is True
        
        # Verify token is gone
        found_user = await get_user_by_token(db_session, token.token)
        assert found_user is None


class TestAuthEndpoints:
    """Tests for auth API endpoints."""
    
    async def test_login_creates_user(self, client):
        """Test login endpoint creates user and returns token."""
        response = await client.post("/api/v1/auth/login", json={"email": "test@example.com"})
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert len(data["token"]) == 36  # UUID
    
    async def test_login_invalid_email(self, client):
        """Test login with invalid email returns error."""
        response = await client.post("/api/v1/auth/login", json={"email": "invalid-email"})

        assert response.status_code == 400

    async def test_login_rejects_bare_at(self, client):
        """Test login with just @ is rejected."""
        response = await client.post("/api/v1/auth/login", json={"email": "@"})
        assert response.status_code == 400

    async def test_login_rejects_double_at(self, client):
        """Test login with double @ is rejected."""
        response = await client.post("/api/v1/auth/login", json={"email": "user@@domain.com"})
        assert response.status_code == 400

    async def test_login_rejects_no_tld(self, client):
        """Test login with no TLD is rejected."""
        response = await client.post("/api/v1/auth/login", json={"email": "a@b"})
        assert response.status_code == 400

    async def test_login_rejects_empty_email(self, client):
        """Test login with empty email returns error."""
        response = await client.post("/api/v1/auth/login", json={"email": ""})
        assert response.status_code == 400
    
    async def test_me_endpoint(self, client):
        """Test /me endpoint returns user info."""
        # Login first
        login_response = await client.post("/api/v1/auth/login", json={"email": "test@example.com"})
        token = login_response.json()["token"]
        
        # Get user info
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    
    async def test_me_without_token(self, client):
        """Test /me endpoint without token returns 401."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_me_with_invalid_token(self, client):
        """Test /me endpoint with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    async def test_logout_endpoint(self, client):
        """Test logout endpoint invalidates token."""
        # Login first
        login_response = await client.post("/api/v1/auth/login", json={"email": "test@example.com"})
        token = login_response.json()["token"]
        
        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify token is invalidated
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 401
    
    async def test_logout_without_token(self, client):
        """Test logout without token returns 401."""
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401
    
    async def test_disabled_user_cannot_access(self, client):
        """Test disabled user gets 403 when accessing protected endpoint."""
        # Login first
        login_response = await client.post("/api/v1/auth/login", json={"email": "test@example.com"})
        token = login_response.json()["token"]
        user_id = login_response.json()["user"]["id"]
        
        # Disable user directly in DB
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one()
            user.is_active = False
            await session.commit()
        
        # Try to access protected endpoint
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
