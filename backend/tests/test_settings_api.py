import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_auth_token, register_user
from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User
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
    from httpx import ASGITransport, AsyncClient

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
        await session.execute(text("DELETE FROM settings"))
        await session.commit()


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession):
    from app.core import config

    original = config._settings
    try:
        config._settings = config.Settings(admin_email="admin@test.com")
        user = await register_user(db_session, "admin@test.com", "password123")
        return user
    finally:
        config._settings = original


@pytest.fixture(scope="function")
async def regular_user(db_session: AsyncSession):
    return await register_user(db_session, "user@test.com", "password123")


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


class TestFeatureFlagsApi:
    async def test_list_feature_flags(self, client, admin_token):
        response = await client.get(
            "/api/v1/settings/feature-flags",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4
        keys = {item["key"] for item in data["items"]}
        assert "ENABLE_CODE_NODE" in keys
        assert "ENABLE_HTTP_NODE" in keys

    async def test_non_admin_cannot_update_feature_flag(self, client, user_token):
        response = await client.put(
            "/api/v1/settings/feature-flags/ENABLE_CODE_NODE",
            json={"enabled": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    async def test_admin_can_update_feature_flag(self, client, admin_token):
        update_resp = await client.put(
            "/api/v1/settings/feature-flags/ENABLE_CODE_NODE",
            json={"enabled": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["enabled"] is True

        list_resp = await client.get(
            "/api/v1/settings/feature-flags",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        flags = {item["key"]: item["enabled"] for item in list_resp.json()["items"]}
        assert flags["ENABLE_CODE_NODE"] is True
