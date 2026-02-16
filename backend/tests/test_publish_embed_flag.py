import json
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from httpx import AsyncClient
from typing import cast

import app.api.publish as publish_api
import app.core.publish_embed as publish_embed
from app.core.database import AsyncSessionLocal, init_db
from main import create_app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
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
        _ = await session.execute(text("DELETE FROM auth_tokens"))
        _ = await session.execute(text("DELETE FROM users"))
        _ = await session.execute(text("DELETE FROM settings"))
        await session.commit()


async def _flag_disabled(_: str) -> bool:
    return False


async def _flag_enabled(_: str) -> bool:
    return True


class TestPublishEmbedFlag:
    async def test_flag_off_blocks_post_and_get(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(publish_api, "is_feature_enabled", _flag_disabled)

        post_resp = await client.post(
            "/api/v1/publish/embed",
            json={"workflow_id": "wf-does-not-matter"},
        )
        assert post_resp.status_code == 403

        get_resp = await client.get("/api/v1/publish/embed/any-token")
        assert get_resp.status_code == 403

    async def test_expired_token_returns_403(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(publish_api, "is_feature_enabled", _flag_enabled)
        monkeypatch.setattr(
            publish_embed, "_store_path", lambda: tmp_path / "embed_tokens.json"
        )

        record = publish_embed.create_embed_token(workflow_id="wf-any", created_by="1")

        store_path = tmp_path / "embed_tokens.json"
        with open(store_path, "r", encoding="utf-8") as handle:
            data_obj = cast(object, json.load(handle))

        assert isinstance(data_obj, dict)
        raw_dict = cast(dict[object, object], data_obj)
        data_map: dict[str, object] = {
            k: v for k, v in raw_dict.items() if isinstance(k, str)
        }
        tokens_obj = data_map.get("tokens")
        assert isinstance(tokens_obj, dict)
        tokens_map = cast(dict[object, object], tokens_obj)
        assert record.token in tokens_map
        entry_obj = tokens_map[record.token]
        assert isinstance(entry_obj, dict)

        entry_obj["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).isoformat()

        with open(store_path, "w", encoding="utf-8") as handle:
            json.dump(data_obj, handle, ensure_ascii=False, indent=2)

        resp = await client.get(f"/api/v1/publish/embed/{record.token}")
        assert resp.status_code == 403
