"""
Knowledge base storage and helper utilities.

This module provides storage operations, path utilities, and helper functions
for the knowledge base API. It separates data persistence concerns from HTTP routing.
"""
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from filelock import FileLock

from app.models.document import DocumentStatus


# Task retention period: 30 minutes
_TASK_RETENTION_SECONDS = 30 * 60

ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# In-memory task tracking (loaded from disk on module init)
processing_tasks: dict[str, dict] = {}


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _get_kb_metadata_file() -> Path:
    """Get the path to KB metadata file."""
    return _get_project_root() / "data" / "kb_metadata.json"


def _get_tasks_file() -> Path:
    """Get the path to tasks persistence file."""
    return _get_project_root() / "data" / "processing_tasks.json"


def load_tasks() -> dict[str, dict]:
    """Load tasks from persistence file."""
    tasks_file = _get_tasks_file()
    lock = FileLock(str(tasks_file) + ".lock")
    with lock:
        if not tasks_file.exists():
            return {}
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def save_tasks(tasks: dict[str, dict]) -> None:
    """Save tasks to persistence file."""
    tasks_file = _get_tasks_file()
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(tasks_file) + ".lock")
    with lock:
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)


def cleanup_old_tasks() -> None:
    """Remove completed/failed tasks older than retention period."""
    global processing_tasks
    now = datetime.now(timezone.utc)
    to_remove = []
    for task_id, task in processing_tasks.items():
        if task.get("status") in ("completed", "failed"):
            started_at = task.get("started_at")
            if started_at:
                try:
                    started = datetime.fromisoformat(started_at)
                    if (now - started).total_seconds() > _TASK_RETENTION_SECONDS:
                        to_remove.append(task_id)
                except (ValueError, TypeError):
                    to_remove.append(task_id)
    for task_id in to_remove:
        del processing_tasks[task_id]
    save_tasks(processing_tasks)


def add_task(task_id: str, task_data: dict) -> None:
    """Add a task to the processing tasks and persist."""
    global processing_tasks
    processing_tasks[task_id] = task_data
    save_tasks(processing_tasks)


def update_task(task_id: str, updates: dict) -> None:
    """Update a task with new data and persist."""
    global processing_tasks
    if task_id in processing_tasks:
        processing_tasks[task_id].update(updates)
        save_tasks(processing_tasks)


def remove_task(task_id: str) -> None:
    """Remove a task from processing tasks and persist."""
    global processing_tasks
    if task_id in processing_tasks:
        del processing_tasks[task_id]
        save_tasks(processing_tasks)


# Load tasks from disk on module initialization
processing_tasks = load_tasks()


def load_kb_metadata() -> dict:
    """Load knowledge base metadata from JSON file."""
    metadata_file = _get_kb_metadata_file()
    lock = FileLock(str(metadata_file) + ".lock")
    with lock:
        if not metadata_file.exists():
            return {}
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def save_kb_metadata(metadata: dict) -> None:
    """Save knowledge base metadata to JSON file."""
    metadata_file = _get_kb_metadata_file()
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(metadata_file) + ".lock")
    with lock:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


def get_kb_document_count(kb_id: str) -> int:
    """Get the number of documents in a knowledge base."""
    return len(load_documents_metadata(kb_id))


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def secure_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal."""
    filename = Path(filename).name
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    filename = filename.lstrip(".")
    filename = " ".join(filename.split())
    return filename or "unnamed_file"


def get_upload_path(kb_id: str, filename: str) -> tuple[Path, str]:
    """Get a safe path for saving an uploaded file."""
    safe_kb_id = re.sub(r"[^\w-]", "", kb_id) or "default"
    project_root = _get_project_root()
    upload_dir = project_root / "data" / "uploads" / safe_kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(filename)
    unique_filename = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    full_path = upload_dir / unique_filename

    try:
        full_path.resolve().relative_to(upload_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid file path detected") from exc

    return full_path, unique_filename


def get_metadata_path(kb_id: str) -> Path:
    """Get the path for document metadata JSON file."""
    safe_kb_id = re.sub(r"[^\w-]", "", kb_id) or "default"
    project_root = _get_project_root()
    metadata_dir = project_root / "data" / "metadata" / safe_kb_id
    metadata_dir.mkdir(parents=True, exist_ok=True)
    return metadata_dir / "documents.json"


def load_documents_metadata(kb_id: str) -> dict:
    """Load document metadata from JSON file."""
    metadata_path = get_metadata_path(kb_id)
    lock = FileLock(str(metadata_path) + ".lock")
    with lock:
        if not metadata_path.exists():
            return {}
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def save_documents_metadata(kb_id: str, metadata: dict) -> None:
    """Save document metadata to JSON file."""
    metadata_path = get_metadata_path(kb_id)
    lock = FileLock(str(metadata_path) + ".lock")
    with lock:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


def update_document_status(
    kb_id: str,
    doc_id: str,
    status: DocumentStatus,
    error_message: str | None = None
) -> None:
    """Update document status in metadata."""
    all_metadata = load_documents_metadata(kb_id)
    if doc_id in all_metadata:
        all_metadata[doc_id]["status"] = status.value
        all_metadata[doc_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        if error_message:
            all_metadata[doc_id]["error_message"] = error_message
        save_documents_metadata(kb_id, all_metadata)


def remove_kb_directories(kb_id: str) -> None:
    """Remove all directories associated with a knowledge base."""
    project_root = _get_project_root()
    upload_dir = project_root / "data" / "uploads" / kb_id
    metadata_dir = project_root / "data" / "metadata" / kb_id

    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    if metadata_dir.exists():
        shutil.rmtree(metadata_dir)


def validate_kb_id(kb_id: str) -> bool:
    """Validate knowledge base ID format."""
    return bool(re.match(r"^[\w-]+$", kb_id))


def get_kb_directories(kb_id: str) -> tuple[Path, Path]:
    """Get upload and metadata directory paths for a knowledge base."""
    project_root = _get_project_root()
    upload_dir = project_root / "data" / "uploads" / kb_id
    metadata_dir = project_root / "data" / "metadata" / kb_id
    return upload_dir, metadata_dir
