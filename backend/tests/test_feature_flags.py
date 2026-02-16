import pytest
from sqlalchemy import text

from app.core import config
from app.core.database import AsyncSessionLocal, init_db
from app.core.feature_flags import (
    FEATURE_FLAG_KEYS,
    _normalize_flag_key,
    _parse_bool,
    get_feature_flag_value,
    list_feature_flags,
    set_feature_flag_value,
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    await init_db()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM settings"))
        await session.commit()


def test_normalize_flag_key_rejects_unknown() -> None:
    assert _normalize_flag_key(" enable_code_node ") == "ENABLE_CODE_NODE"
    with pytest.raises(ValueError):
        _normalize_flag_key("ENABLE_DOES_NOT_EXIST")


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, True),
        (False, False),
        ("true", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("0", False),
        ("off", False),
        ("no", False),
    ],
)
def test_parse_bool(value, expected) -> None:
    assert _parse_bool(value) is expected


@pytest.mark.asyncio
async def test_get_feature_flag_uses_default_settings_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = config._settings
    try:
        config._settings = config.Settings(
            enable_code_node=True,
            enable_http_node=False,
            enable_openai_api=False,
            enable_public_embed=False,
        )

        async with AsyncSessionLocal() as session:
            assert await get_feature_flag_value(session, "ENABLE_CODE_NODE") is True
            assert await get_feature_flag_value(session, "ENABLE_HTTP_NODE") is False
    finally:
        config._settings = original


@pytest.mark.asyncio
async def test_set_and_list_feature_flags_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = config._settings
    try:
        config._settings = config.Settings(
            enable_code_node=False,
            enable_http_node=False,
            enable_openai_api=False,
            enable_public_embed=False,
        )

        async with AsyncSessionLocal() as session:
            assert (
                await set_feature_flag_value(session, "ENABLE_CODE_NODE", True) is True
            )
            assert (
                await set_feature_flag_value(session, "ENABLE_CODE_NODE", False)
                is False
            )
            flags = await list_feature_flags(session)

        assert set(flags.keys()) == set(FEATURE_FLAG_KEYS)
        assert flags["ENABLE_CODE_NODE"] is False
    finally:
        config._settings = original
