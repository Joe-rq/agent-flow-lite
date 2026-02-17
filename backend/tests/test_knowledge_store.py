from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.knowledge import store
from app.models.document import DocumentStatus


def test_allowed_file_and_secure_filename() -> None:
    assert store.allowed_file("a.md") is True
    assert store.allowed_file("a.exe") is False
    assert store._secure_filename("../../evil?.md") == "evil.md"


def test_get_upload_path_sanitizes_kb_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "_get_project_root", lambda: tmp_path)

    full_path, unique_name = store.get_upload_path("kb/../bad", "../a b?.md")

    assert full_path.parent == tmp_path / "data" / "uploads" / "kbbad"
    assert unique_name.endswith("_a b.md")
    assert full_path.parent.exists()


def test_cleanup_old_tasks_removes_expired_and_invalid_started_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(hours=1)).isoformat()
    new_time = (now - timedelta(minutes=5)).isoformat()

    store.processing_tasks = {
        "old-completed": {"status": "completed", "started_at": old_time},
        "recent-completed": {"status": "completed", "started_at": new_time},
        "invalid-failed": {"status": "failed", "started_at": "not-a-time"},
        "running": {"status": "running", "started_at": old_time},
    }
    saved: dict[str, dict[str, object]] = {}

    def _save_tasks(tasks: dict[str, dict[str, object]]) -> None:
        saved.clear()
        saved.update(tasks)

    monkeypatch.setattr(store, "save_tasks", _save_tasks)

    store.cleanup_old_tasks()

    assert "old-completed" not in store.processing_tasks
    assert "invalid-failed" not in store.processing_tasks
    assert "recent-completed" in store.processing_tasks
    assert "running" in store.processing_tasks
    assert saved == store.processing_tasks


def test_update_document_status_updates_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = {
        "doc-1": {
            "status": "processing",
            "updated_at": "2026-02-17T00:00:00+00:00",
        }
    }
    captured: dict[str, dict[str, object]] = {}

    monkeypatch.setattr(store, "load_documents_metadata", lambda _kb: metadata)
    monkeypatch.setattr(
        store,
        "save_documents_metadata",
        lambda _kb, payload: captured.update(payload),
    )

    store.update_document_status("kb-1", "doc-1", DocumentStatus.FAILED, "boom")

    assert captured["doc-1"]["status"] == "failed"
    assert captured["doc-1"]["error_message"] == "boom"
    assert "updated_at" in captured["doc-1"]
