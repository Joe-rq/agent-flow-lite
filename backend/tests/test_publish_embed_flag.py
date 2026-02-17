import json
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from starlette.requests import Request

from httpx import AsyncClient
from typing import cast

import app.api.publish as publish_api
import app.core.publish_embed as publish_embed
from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User
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


def _fake_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_publish_embed_returns_404_when_workflow_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _missing(_workflow_id: str):
        raise HTTPException(status_code=404, detail="Workflow not found")

    monkeypatch.setattr(publish_api.workflow_api, "get_workflow_for_internal", _missing)

    request = _fake_request()
    user = User(id=1, email="owner@example.com")
    payload = publish_api.PublishEmbedRequest(workflow_id="wf-missing")

    with pytest.raises(HTTPException) as exc:
        await publish_api.publish_embed(request=request, payload=payload, user=user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_view_embed_rejects_too_large_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Record:
        workflow_id = "wf-1"

    monkeypatch.setattr(publish_api, "get_valid_embed_record", lambda _token: _Record())

    request = _fake_request()
    with pytest.raises(HTTPException) as exc:
        await publish_api.view_embed(
            request=request,
            token="ok-token",
            input="x" * (publish_api.MAX_INPUT_CHARS + 1),
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_view_embed_success_renders_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Record:
        workflow_id = "wf-1"

    async def _execute_once(*, workflow_id: str, input_text: str) -> str:
        _ = workflow_id
        return f"echo:{input_text}"

    monkeypatch.setattr(publish_api, "get_valid_embed_record", lambda _token: _Record())
    monkeypatch.setattr(publish_api, "_execute_workflow_once", _execute_once)

    request = _fake_request()
    resp = await publish_api.view_embed(
        request=request, token="ok-token", input="hello"
    )

    assert resp.status_code == 200
    body = bytes(resp.body).decode("utf-8")
    assert "<h2>Output</h2>" in body
    assert "echo:hello" in body
