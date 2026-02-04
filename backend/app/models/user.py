"""
User and authentication models.

Provides SQLAlchemy models for users and auth tokens with soft delete support.
"""
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(PyEnum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    User model with soft delete support.
    
    Attributes:
        id: Auto-incrementing primary key
        email: Normalized email address (unique)
        role: User role (admin or user)
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        deleted_at: Timestamp for soft delete (null if active)
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.USER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationship to auth tokens
    auth_tokens: Mapped[list["AuthToken"]] = relationship(
        "AuthToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if user is soft deleted."""
        return self.deleted_at is not None

    def normalize_email(self) -> str:
        """Normalize email to lowercase and strip whitespace."""
        return self.email.lower().strip()

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class AuthToken(Base):
    """
    Authentication token model.
    
    Attributes:
        id: Auto-incrementing primary key
        token: UUID token string (unique)
        user_id: Foreign key to users table
        created_at: Timestamp when token was created
        expires_at: Timestamp when token expires (7 days from creation)
    """
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )

    # Relationship to user
    user: Mapped["User"] = relationship("User", back_populates="auth_tokens")

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        # Handle both timezone-aware and naive datetimes
        now = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            now = now.replace(tzinfo=None)
        return now > self.expires_at

    def __repr__(self) -> str:
        return f"<AuthToken(token={self.token[:8]}..., user_id={self.user_id})>"
