"""Zep session memory client wrapper."""

from __future__ import annotations

import inspect
from typing import Any, Iterable, Optional, TypedDict

from app.core.config import Settings, settings


class ZepMessageInput(TypedDict, total=False):
    role_type: str
    role: str
    content: str
    metadata: dict[str, Any]


class ZepClient:
    def __init__(self, app_settings: Settings) -> None:
        self._settings = app_settings
        self._client: Any | None = None

    @property
    def enabled(self) -> bool:
        return bool(self._settings.zep_enabled and self._settings.zep_api_key)

    def _create_client(self) -> Any:
        from zep_cloud import Zep

        kwargs: dict[str, Any] = {
            "api_key": self._settings.zep_api_key,
        }
        try:
            parameters = inspect.signature(Zep).parameters
        except (TypeError, ValueError):
            parameters = {}
        if "api_url" in parameters:
            kwargs["api_url"] = self._settings.zep_api_url
        return Zep(**kwargs)

    def _get_client(self) -> Any | None:
        if not self.enabled:
            return None
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def ensure_user_session(self, user_id: str, session_id: str) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            if hasattr(client, "user") and hasattr(client.user, "add"):
                client.user.add(user_id=user_id)
            if hasattr(client, "memory") and hasattr(client.memory, "add_session"):
                client.memory.add_session(user_id=user_id, session_id=session_id)
            return True
        except Exception:
            return False

    def add_messages(self, session_id: str, messages: Iterable[ZepMessageInput]) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            from zep_cloud.types import Message

            zep_messages = [
                Message(
                    role_type=msg.get("role_type", "user"),
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    metadata=msg.get("metadata"),
                )
                for msg in messages
            ]
            client.memory.add(session_id=session_id, messages=zep_messages)
            return True
        except Exception:
            return False

    def get_memory_context(self, session_id: str) -> str:
        client = self._get_client()
        if client is None:
            return ""
        try:
            memory = client.memory.get(session_id=session_id)
            context = getattr(memory, "context", "")
            return context or ""
        except Exception:
            return ""


_zep_client: ZepClient | None = None


def zep_client() -> ZepClient:
    global _zep_client
    if _zep_client is None:
        _zep_client = ZepClient(settings())
    return _zep_client
