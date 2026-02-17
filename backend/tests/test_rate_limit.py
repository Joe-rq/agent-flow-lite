from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.middleware.rate_limit import (
    _async_lookup_user_id,
    _sync_lookup_user_id,
    _token_user_cache,
    get_rate_limit_key,
)


def _make_request(
    token: str | None = None,
    remote_addr: str = "1.2.3.4",
    state_user_id: int | None = None,
) -> MagicMock:
    request = MagicMock()
    headers: dict[str, str] = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request.headers = headers
    request.client.host = remote_addr

    state = MagicMock()
    if state_user_id is not None:
        state.rate_limit_user_id = state_user_id
    else:
        del state.rate_limit_user_id
    request.state = state
    return request


def test_middleware_resolved_user_id_is_primary_key() -> None:
    """When middleware has set rate_limit_user_id, use it directly."""
    key = get_rate_limit_key(_make_request(token="any-token", state_user_id=42))
    assert key == "user:42"


def test_same_user_different_tokens_same_key(monkeypatch) -> None:
    """Two tokens belonging to the same user must produce the same rate limit key."""
    monkeypatch.setattr(
        "app.middleware.rate_limit._sync_lookup_user_id",
        lambda token: 42,
    )
    key_a = get_rate_limit_key(_make_request(token="token-aaa"))
    key_b = get_rate_limit_key(_make_request(token="token-bbb"))
    assert key_a == key_b == "user:42"


def test_different_users_different_keys(monkeypatch) -> None:
    """Tokens from different users must produce different rate limit keys."""
    user_map = {"token-alice": 1, "token-bob": 2}
    monkeypatch.setattr(
        "app.middleware.rate_limit._sync_lookup_user_id",
        lambda token: user_map.get(token),
    )
    key_a = get_rate_limit_key(_make_request(token="token-alice"))
    key_b = get_rate_limit_key(_make_request(token="token-bob"))
    assert key_a != key_b
    assert key_a == "user:1"
    assert key_b == "user:2"


def test_unknown_token_falls_back_to_hmac(monkeypatch) -> None:
    """Token not in DB should produce an HMAC-based key, not raw token."""
    monkeypatch.setattr(
        "app.middleware.rate_limit._sync_lookup_user_id",
        lambda token: None,
    )
    key = get_rate_limit_key(_make_request(token="unknown-token"))
    assert key.startswith("token:")
    assert "unknown-token" not in key


def test_no_token_uses_ip() -> None:
    """Request without Authorization header should use client IP."""
    key = get_rate_limit_key(_make_request(token=None, remote_addr="10.0.0.1"))
    assert key == "10.0.0.1"


def test_sync_lookup_caches(monkeypatch) -> None:
    """Successful sync lookups should be cached."""
    _token_user_cache.clear()
    monkeypatch.setattr(
        "app.middleware.rate_limit.sqlite3.connect",
        _fake_connect_factory({"tok-1": 99}),
    )
    assert _sync_lookup_user_id("tok-1") == 99
    assert "tok-1" in _token_user_cache
    assert _token_user_cache["tok-1"] == 99
    _token_user_cache.clear()


@pytest.mark.asyncio
async def test_async_lookup_uses_cache() -> None:
    """Async lookup should return cached value without DB query."""
    _token_user_cache.clear()
    _token_user_cache["cached-tok"] = 77
    result = await _async_lookup_user_id("cached-tok")
    assert result == 77
    _token_user_cache.clear()


def _fake_connect_factory(token_map: dict[str, int]):
    class FakeCursor:
        def __init__(self, token: str):
            self._token = token
            self._map = token_map

        def fetchone(self):
            uid = self._map.get(self._token)
            return (uid,) if uid is not None else None

    class FakeConn:
        def execute(self, query, params):
            return FakeCursor(params[0])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def connect(*args, **kwargs):
        return FakeConn()

    return connect
