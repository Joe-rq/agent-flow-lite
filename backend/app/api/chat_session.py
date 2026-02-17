"""
Chat session management with database storage.

Provides async session CRUD operations using SQLAlchemy,
replacing the previous file-based JSON + filelock approach.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User
from app.core.database import AsyncSessionLocal
from app.models.chat import ChatMessage, SessionHistory
from app.models.session import ChatSessionDB
from app.models.user import UserRole

logger = logging.getLogger(__name__)

EXCERPT_LIMIT = 200


def check_session_ownership(session: SessionHistory, user: User) -> bool:
    """Check if a user owns a session or is an admin."""
    if user.role == UserRole.ADMIN:
        return True
    if session.user_id is None:
        return True
    return session.user_id == str(user.id)


def _db_to_pydantic(row: ChatSessionDB) -> SessionHistory:
    """Convert ORM row to Pydantic SessionHistory."""
    messages_raw = json.loads(row.messages_json) if row.messages_json else []
    messages = []
    for m in messages_raw:
        if isinstance(m, dict):
            if m.get("timestamp") and isinstance(m["timestamp"], str):
                m["timestamp"] = datetime.fromisoformat(m["timestamp"])
            messages.append(ChatMessage(**m))
    return SessionHistory(
        session_id=row.session_id,
        messages=messages,
        created_at=row.created_at or datetime.now(timezone.utc),
        updated_at=row.updated_at,
        kb_id=row.kb_id,
        workflow_id=row.workflow_id,
        user_id=row.user_id,
    )


async def load_session(session_id: str) -> Optional[SessionHistory]:
    """Load session from database."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChatSessionDB).where(ChatSessionDB.session_id == session_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _db_to_pydantic(row)


async def save_session(session: SessionHistory) -> None:
    """Save session to database (upsert)."""
    now = datetime.now(timezone.utc)
    session.updated_at = now
    messages_json = json.dumps(
        session.model_dump(mode="json")["messages"], ensure_ascii=False
    )
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChatSessionDB).where(ChatSessionDB.session_id == session.session_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ChatSessionDB(
                session_id=session.session_id,
                user_id=session.user_id,
                kb_id=session.kb_id,
                workflow_id=session.workflow_id,
                messages_json=messages_json,
                created_at=session.created_at,
                updated_at=now,
            )
            db.add(row)
        else:
            row.messages_json = messages_json
            row.updated_at = now
            row.kb_id = session.kb_id
            row.workflow_id = session.workflow_id
            if session.user_id is not None:
                row.user_id = session.user_id
        await db.commit()


async def list_user_sessions(user: User) -> list[dict[str, object]]:
    """List sessions for a user (admin sees all)."""
    async with AsyncSessionLocal() as db:
        query = select(ChatSessionDB)
        if user.role != UserRole.ADMIN:
            user_id_str = str(user.id)
            query = query.where(
                (ChatSessionDB.user_id == user_id_str)
                | (ChatSessionDB.user_id.is_(None))
            )
        result = await db.execute(query)
        rows = result.scalars().all()

    sessions = []
    for row in rows:
        sh = _db_to_pydantic(row)
        title = ""
        for msg in sh.messages:
            if msg.role == "user":
                title = msg.content
                break
        sessions.append(
            {
                "session_id": sh.session_id,
                "title": title,
                "created_at": sh.created_at.isoformat(),
                "updated_at": (
                    sh.updated_at.isoformat()
                    if sh.updated_at
                    else sh.created_at.isoformat()
                ),
                "message_count": len(sh.messages),
                "kb_id": sh.kb_id,
                "workflow_id": sh.workflow_id,
                "user_id": sh.user_id,
            }
        )
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    return sessions


async def delete_session_by_id(session_id: str) -> bool:
    """Delete a session from the database. Returns True if deleted."""
    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(ChatSessionDB.id).where(ChatSessionDB.session_id == session_id)
        )
        if existing.first() is None:
            return False
        await db.execute(
            sa_delete(ChatSessionDB).where(ChatSessionDB.session_id == session_id)
        )
        await db.commit()
        return True
