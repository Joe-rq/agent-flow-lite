"""
Database configuration and session management.

Provides SQLAlchemy async engine and session setup for SQLite database.
"""
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Database file location - store in data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR / 'app.db'}"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base class for declarative models
Base = declarative_base()


async def init_db() -> None:
    """Initialize database by creating all tables and running migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate: add password_hash column if missing (SQLite create_all won't alter existing tables)
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        if "password_hash" not in columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128)"))


async def get_db():
    """
    Dependency for getting async database session.
    
    Yields:
        AsyncSession: Database session that auto-closes on completion.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
