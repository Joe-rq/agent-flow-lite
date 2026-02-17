"""
FastAPI Backend Application
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.api.publish import router as publish_router
from app.api.settings import router as settings_router
from app.api.skill import router as skill_router
from app.api.workflow import router as workflow_router
from app.core.auth import cleanup_expired_tokens
from app.core.database import AsyncSessionLocal, init_db
from app.core.safety_check import run_safety_checks
from app.middleware.rate_limit import setup_rate_limiting

# Load environment variables
_ = load_dotenv()

logger = logging.getLogger(__name__)

TOKEN_CLEANUP_INTERVAL = 6 * 3600  # 6 hours


def _run_alembic_upgrade() -> None:
    cfg = Config(str(Path(__file__).with_name("alembic.ini")))
    cfg.set_main_option("script_location", str(Path(__file__).with_name("alembic")))
    command.upgrade(cfg, "head")


async def _periodic_token_cleanup() -> None:
    """Periodically delete expired authentication tokens."""
    while True:
        await asyncio.sleep(TOKEN_CLEANUP_INTERVAL)
        try:
            async with AsyncSessionLocal() as db:
                count = await cleanup_expired_tokens(db)
                if count > 0:
                    logger.info("Cleaned up %d expired tokens", count)
        except Exception:
            logger.exception("Token cleanup failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context manager"""
    # Startup: Initialize resources
    await asyncio.to_thread(_run_alembic_upgrade)
    await init_db()
    run_safety_checks()
    cleanup_task = asyncio.create_task(_periodic_token_cleanup())
    yield
    # Shutdown: Cleanup resources
    _ = cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Agent Flow Lite API",
        description="Backend API for Agent Flow Lite",
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_rate_limiting(app)

    # Configure CORS
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "Agent Flow Lite API",
            "version": "0.1.0",
            "status": "running",
        }

    _ = root

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    _ = health_check

    app.include_router(auth_router)
    app.include_router(workflow_router)
    app.include_router(knowledge_router)
    app.include_router(settings_router)
    app.include_router(skill_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(publish_router)

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "true").lower() == "true",
    )
