from types import SimpleNamespace

from app.core.config import Settings
from app.core.zep import ZepClient


def test_zep_settings_defaults() -> None:
    settings = Settings()
    assert settings.zep_api_key == ""
    assert settings.zep_api_url == "https://api.getzep.com"
    assert settings.zep_enabled is False


def test_zep_client_disabled_mode() -> None:
    settings = Settings(zep_api_key="", zep_enabled=False)
    client = ZepClient(settings)

    assert client.enabled is False
    assert client.ensure_user_session("user-1", "session-1") is False
    assert client.add_messages("session-1", []) is False
    assert client.get_memory_context("session-1") == ""


def test_zep_client_enabled_mode(monkeypatch) -> None:
    class FakeUser:
        def __init__(self) -> None:
            self.added = []

        def add(self, user_id: str) -> None:
            self.added.append(user_id)

    class FakeMemory:
        def __init__(self) -> None:
            self.sessions = []
            self.messages = []

        def add_session(self, user_id: str, session_id: str) -> None:
            self.sessions.append((user_id, session_id))

        def add(self, session_id: str, messages: list) -> None:
            self.messages.append((session_id, messages))

        def get(self, session_id: str) -> SimpleNamespace:
            return SimpleNamespace(context="Memory context")

    class FakeZep:
        def __init__(self, **_kwargs) -> None:
            self.user = FakeUser()
            self.memory = FakeMemory()

    import zep_cloud

    monkeypatch.setattr(zep_cloud, "Zep", FakeZep)

    settings = Settings(zep_api_key="key", zep_enabled=True)
    client = ZepClient(settings)

    assert client.enabled is True
    assert client.ensure_user_session("user-1", "session-1") is True
    assert client.add_messages(
        "session-1",
        [{"role_type": "user", "role": "user-1", "content": "hi"}]
    ) is True
    assert client.get_memory_context("session-1") == "Memory context"
