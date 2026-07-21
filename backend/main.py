"""
main.py - FastAPI Application Entry Point (Phase 2 + Phase 3)

This module is the ASGI entry point for the AI Resume Analyzer backend.

Responsibilities:
  - Instantiate the FastAPI application with metadata (title, version, description).
  - Configure CORS middleware to allow cross-origin requests from the frontend.
  - Register the API router (from app/api/routes.py) under the /api prefix.
  - Pre-load the sentence-transformer embedding model during startup (Phase 3).
  - Mount the frontend/ directory as static files so the UI is served from
    http://127.0.0.1:8000/ when accessed via a browser.

Usage:
    python -m uvicorn backend.main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.config import API_DESCRIPTION, API_TITLE, API_VERSION
from backend.app.services.embedding_service import load_model as load_embedding_model

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
# Configure the root logger once here so every child logger in the app
# (backend.app.services.*, backend.app.api.*) inherits this format and level.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Startup / Shutdown Lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    """FastAPI lifespan context manager.

    Runs startup logic before the first request is served and shutdown
    logic after the last request completes.

    Startup:
      - Load the sentence-transformer embedding model into memory once.
        This prevents a 1-2 second cold-start on the first /api/analyze call.

    Shutdown:
      - (Reserved for future cleanup: DB connection pools, file handles, etc.)
    """
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("AI Resume Analyzer — Phase 3 starting up")
    logger.info("=" * 60)

    try:
        load_embedding_model()
        logger.info("Startup complete — embedding model ready.")
    except RuntimeError as exc:
        # Log the error but do NOT crash the server — /api/upload still works
        # without the embedding model.  /api/analyze will return HTTP 500 if
        # the model failed to load.
        logger.error(
            "Startup WARNING: embedding model failed to load: %s", exc)

    yield  # Server is now handling requests

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("AI Resume Analyzer shutting down.")

# ---------------------------------------------------------------------------
# Application Instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    # Swagger UI will be served at /docs; ReDoc at /redoc
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------

# Allow all origins during development.
# In production, replace "*" with the exact frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # permits any origin — fine for local dev
    allow_credentials=False,
    allow_methods=["*"],          # GET, POST, OPTIONS, etc.
    allow_headers=["*"],          # Content-Type, Authorization, etc.
)

# ---------------------------------------------------------------------------
# API Router
# ---------------------------------------------------------------------------

# The router already has the /api prefix defined internally in routes.py
app.include_router(router)

# ---------------------------------------------------------------------------
# Static Frontend (optional — only mounted if the frontend/ directory exists)
# ---------------------------------------------------------------------------

# Resolve the frontend folder relative to this file's parent (project root)
FRONTEND_DIR: Path = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.is_dir():
    # Serve the frontend at / — must be mounted AFTER the API router so that
    # /api/* routes are not swallowed by the static file handler.
    app.mount(
        "/",
        StaticFiles(
            directory=str(FRONTEND_DIR),
            html=True),
        name="frontend")
