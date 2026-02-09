"""
Chat session management for persistent conversation history.

This module provides session CRUD operations including load, save, list,
and delete functionality with file-based storage and ownership checks.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from filelock import FileLock

from app.core.auth import User
from app.models.user import UserRole
from app.models.chat import SessionHistory

logger = logging.getLogger(__name__)

# Constants
EXCERPT_LIMIT = 200
SESSIONS_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_session_path(session_id: str) -> Path:
    """
    Get the file path for a session.

    Args:
        session_id: Session identifier (must be validated by pattern constraint first)

    Returns:
        Path object for the session file

    Raises:
        ValueError: If session_id attempts path traversal
    """
    session_file = SESSIONS_DIR / f"{session_id}.json"
    try:
        # Containment check: ensure resolved path stays within SESSIONS_DIR
        session_file.resolve().relative_to(SESSIONS_DIR.resolve())
    except ValueError:
        # Fail-closed behavior: reject any path traversal attempt
        raise ValueError(f"Invalid session_id: {session_id}") from None
    return session_file


def check_session_ownership(session: SessionHistory, user: User) -> bool:
    """
    Check if a user owns a session or is an admin.

    Args:
        session: The session to check
        user: The current authenticated user

    Returns:
        True if user owns the session or is admin, False otherwise
    """
    # Admin can access any session
    if user.role == UserRole.ADMIN:
        return True

    # If session has no user_id, treat as orphaned - allow access for backward compatibility
    # but ideally should be migrated
    if session.user_id is None:
        return True

    # Check if user owns the session
    return session.user_id == str(user.id)


def load_session(session_id: str) -> Optional[SessionHistory]:
    """Load session history from JSON file."""
    session_path = get_session_path(session_id)
    lock = FileLock(str(session_path) + ".lock")
    with lock:
        if not session_path.exists():
            return None
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Parse timestamps back to datetime objects
                for msg in data.get("messages", []):
                    if msg.get("timestamp"):
                        msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
                if data.get("created_at"):
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                if data.get("updated_at"):
                    data["updated_at"] = datetime.fromisoformat(data["updated_at"])
                return SessionHistory(**data)
        except (json.JSONDecodeError, IOError, ValueError):
            return None


def save_session(session: SessionHistory) -> None:
    """Save session history to JSON file."""
    session_path = get_session_path(session.session_id)
    session.updated_at = datetime.now(timezone.utc)
    lock = FileLock(str(session_path) + ".lock")
    with lock:
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
