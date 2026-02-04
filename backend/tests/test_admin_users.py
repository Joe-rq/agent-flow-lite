import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_auth_token, get_or_create_user
from app.core.database import AsyncSessionLocal, init_db
from app.core.config import settings
from app.models.user import User, UserRole
from main import create_app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client():
    from httpx import AsyncClient, ASGITransport
    
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    await init_db()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM auth_tokens"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession):
    admin_email = settings().admin_email
    user = await get_or_create_user(db_session, admin_email)
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def regular_user(db_session: AsyncSession):
    user = await get_or_create_user(db_session, "user@example.com")
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def admin_token(db_session: AsyncSession, admin_user: User):
    token = await create_auth_token(db_session, admin_user.id)
    await db_session.commit()
    return token.token


@pytest.fixture(scope="function")
async def user_token(db_session: AsyncSession, regular_user: User):
    token = await create_auth_token(db_session, regular_user.id)
    await db_session.commit()
    return token.token


class TestListUsers:
    async def test_admin_can_list_users(self, client, admin_token, regular_user):
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1
    
    async def test_non_admin_cannot_list_users(self, client, user_token):
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    async def test_list_users_without_auth(self, client):
        response = await client.get("/api/v1/admin/users")
        
        assert response.status_code == 401
    
    async def test_list_users_excludes_deleted(self, client, admin_token, db_session: AsyncSession):
        from datetime import datetime, timezone
        
        user = await get_or_create_user(db_session, "deleted@example.com")
        user.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        emails = [u["email"] for u in data["users"]]
        assert "deleted@example.com" not in emails


class TestDisableUser:
    async def test_admin_can_disable_user(self, client, admin_token, regular_user):
        response = await client.post(
            f"/api/v1/admin/users/{regular_user.id}/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "disabled" in data["message"].lower()
    
    async def test_non_admin_cannot_disable_user(self, client, user_token, admin_user):
        response = await client.post(
            f"/api/v1/admin/users/{admin_user.id}/disable",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    async def test_admin_cannot_disable_self(self, client, admin_token, admin_user):
        response = await client.post(
            f"/api/v1/admin/users/{admin_user.id}/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "Cannot disable yourself" in response.json()["detail"]
    
    async def test_disable_already_disabled_user(self, client, admin_token, regular_user, db_session: AsyncSession):
        regular_user.is_active = False
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/admin/users/{regular_user.id}/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "already disabled" in response.json()["detail"]
    
    async def test_disable_nonexistent_user(self, client, admin_token):
        response = await client.post(
            "/api/v1/admin/users/99999/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestEnableUser:
    async def test_admin_can_enable_user(self, client, admin_token, regular_user, db_session: AsyncSession):
        regular_user.is_active = False
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/admin/users/{regular_user.id}/enable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "enabled" in data["message"].lower()
    
    async def test_non_admin_cannot_enable_user(self, client, user_token, regular_user, db_session: AsyncSession):
        regular_user.is_active = False
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/admin/users/{regular_user.id}/enable",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    async def test_enable_already_enabled_user(self, client, admin_token, regular_user):
        response = await client.post(
            f"/api/v1/admin/users/{regular_user.id}/enable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "already enabled" in response.json()["detail"]
    
    async def test_enable_nonexistent_user(self, client, admin_token):
        response = await client.post(
            "/api/v1/admin/users/99999/enable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestDeleteUser:
    async def test_admin_can_delete_user(self, client, admin_token, regular_user):
        response = await client.delete(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()
    
    async def test_non_admin_cannot_delete_user(self, client, user_token, admin_user):
        response = await client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    async def test_admin_cannot_delete_self(self, client, admin_token, admin_user):
        response = await client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "Cannot delete yourself" in response.json()["detail"]
    
    async def test_delete_nonexistent_user(self, client, admin_token):
        response = await client.delete(
            "/api/v1/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    async def test_deleted_user_not_in_list(self, client, admin_token, regular_user):
        await client.delete(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        emails = [u["email"] for u in data["users"]]
        assert regular_user.email not in emails


class TestUserResponseFormat:
    async def test_user_list_item_format(self, client, admin_token, regular_user):
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        user_data = next(u for u in data["users"] if u["email"] == "user@example.com")
        
        assert "id" in user_data
        assert "email" in user_data
        assert "role" in user_data
        assert "is_active" in user_data
        assert "created_at" in user_data
        
        assert isinstance(user_data["id"], int)
        assert isinstance(user_data["email"], str)
        assert user_data["role"] in ["admin", "user"]
        assert isinstance(user_data["is_active"], bool)
        assert isinstance(user_data["created_at"], str)
    
    async def test_user_role_values(self, client, admin_token, admin_user, regular_user):
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        admin_data = next(u for u in data["users"] if u["email"] == admin_user.email)
        user_data = next(u for u in data["users"] if u["email"] == regular_user.email)
        
        assert admin_data["role"] == "admin"
        assert user_data["role"] == "user"
