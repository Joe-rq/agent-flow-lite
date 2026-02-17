"""Chat session ORM model for database storage."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatSessionDB(Base):
    """Persistent chat session stored in the database."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    kb_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    messages_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
