"""
main.py - Production FastAPI Application Entry Point (Phase A DevOps Foundation)

 ASGI entry point for ResumeSphere AI.

Responsibilities:
  - Instantiate FastAPI with production metadata.
  - Track application startup time and uptime.
  - Implement security middleware (Security Headers & CORS).
  - Pre-load sentence-transformer embedding model on startup.
  - Expose production /health endpoint for Docker HEALTHCHECK & monitoring.
  - Mount static frontend interface.
"""

import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.api.routes import router
from backend.app.config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    ALLOWED_ORIGINS,
    APP_ENV,
    DEBUG,
    RATE_LIMIT_ENABLED,
    CORS_ORIGINS,
)
from backend.app.services.embedding_service import load_model as load_embedding_model

# ---------------------------------------------------------------------------
# Structured Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("resumesphere.main")

# Track application start timestamp for /health uptime metrics
START_TIME: float = time.time()
MODEL_LOADED: bool = False


# ---------------------------------------------------------------------------
# Startup / Shutdown Lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    """FastAPI lifespan context manager for startup and graceful shutdown."""
    global MODEL_LOADED, START_TIME
    START_TIME = time.time()

    logger.info("=" * 60)
    logger.info("ResumeSphere AI v%s [%s] initializing", API_VERSION, APP_ENV)
    logger.info("=" * 60)

    try:
        load_embedding_model()
        MODEL_LOADED = True
        logger.info("Startup complete — Sentence Transformer model ready.")
    except Exception as exc:
        MODEL_LOADED = False
        logger.error("Startup WARNING: embedding model pre-load failed: %s", exc)

    yield  # Server serves incoming HTTP requests

    # Shutdown logic
    logger.info("ResumeSphere AI application gracefully shutting down.")


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces essential production security HTTP response headers."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# ---------------------------------------------------------------------------
# Application Instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=DEBUG,
)

# Add Security Headers & CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if APP_ENV == "production" else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if RATE_LIMIT_ENABLED and request.url.path.startswith("/api/"):
            client_ip = request.client.host if request.client else "unknown"
            if client_ip == "blocked.ip.address":
                return Response("Too Many Requests", status_code=429)
        return await call_next(request)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# ---------------------------------------------------------------------------
# Health Monitoring Endpoint (Module A5 & Docker HEALTHCHECK target)
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health Monitoring"],
    summary="Production Health & Readiness Check",
)
async def health_check() -> dict[str, Any]:
    """Returns application health, uptime, environment, and readiness status."""
    uptime = round(time.time() - START_TIME, 2)
    return {
        "status": "ok",
        "app": API_TITLE,
        "version": API_VERSION,
        "environment": APP_ENV,
        "uptime_seconds": uptime,
        "model_loaded": MODEL_LOADED,
    }


# ---------------------------------------------------------------------------
# API Router Registration
# ---------------------------------------------------------------------------
app.include_router(router)

from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_enterprise import router as enterprise_router
from backend.app.api.routes_ecosystem import router as ecosystem_router
from backend.app.api.routes_cloud import router as cloud_router
from backend.app.api.routes_talent import router as talent_router
from backend.app.api.routes_learning import router as learning_router
from backend.app.api.routes_marketplace import router as marketplace_router
from backend.app.api.routes_network import router as network_router
from backend.app.api.routes_copilot import router as copilot_router
from backend.app.api.routes_saas import router as saas_router
from backend.app.api.routes_platform import router as platform_router

app.include_router(auth_router)
app.include_router(enterprise_router)
app.include_router(ecosystem_router)
app.include_router(cloud_router)
app.include_router(talent_router)
app.include_router(learning_router)
app.include_router(marketplace_router)
app.include_router(network_router)
app.include_router(copilot_router)
app.include_router(saas_router)
app.include_router(platform_router)

# ---------------------------------------------------------------------------
# Static Frontend Handler
# ---------------------------------------------------------------------------
FRONTEND_DIR: Path = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
