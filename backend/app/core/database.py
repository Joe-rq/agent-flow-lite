"""
Database configuration and session management.

Provides SQLAlchemy async engine and session setup for SQLite database.
"""

from pathlib import Path

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


def _import_all_models() -> None:
    """Auto-discover and import all modules under app.models.

    This ensures every SQLAlchemy model that subclasses Base is registered
    in Base.metadata before create_all() or Alembic autogenerate runs.
    """
    import importlib
    import pkgutil

    import app.models as models_pkg

    for module_info in pkgutil.iter_modules(models_pkg.__path__):
        importlib.import_module(f"app.models.{module_info.name}")


async def init_db() -> None:
    """Initialize database by creating all tables.

    Uses auto-discovery to import every module in app/models/, so new ORM
    models are picked up automatically without manual imports.
    """
    _import_all_models()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
