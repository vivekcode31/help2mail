"""
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, campaign, status
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db.session import init_db, close_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup / shutdown lifecycle."""
    logger.info("application_starting")
    await init_db()
    logger.info("database_initialised")
    yield
    await close_db()
    logger.info("application_shutting_down")


settings = get_settings()

app = FastAPI(
    title="Help2Mail — Bulk Email Campaign API",
    version="1.0.0",
    description=(
        "Upload an Excel/CSV with company names & emails, attach your resume, "
        "and send personalised job-application emails from your own Gmail account."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="help2mail_session",
    max_age=86400,  # 24 hours
    same_site="lax",
    https_only=settings.is_production,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/v1")
app.include_router(campaign.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api/v1")


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    """Root health-check endpoint."""
    return {"status": "ok", "service": "help2mail"}
