import os
from pathlib import Path

# Load .env file if available
try:
    from dotenv import load_dotenv  # type: ignore[import-not-found,import-untyped]
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Base Paths
# ---------------------------------------------------------------------------

# Root of the backend/ package (the directory where this file lives)
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Folder where uploaded resume PDF files will be stored
UPLOAD_FOLDER: Path = BASE_DIR / "uploads"

# ---------------------------------------------------------------------------
# Auto-create required directories
# ---------------------------------------------------------------------------

# Ensure the uploads directory exists; create it (and any parents) if missing
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# File-type Restrictions
# ---------------------------------------------------------------------------

# Only PDF files are accepted by the upload endpoint
ALLOWED_CONTENT_TYPE: str = "application/pdf"
ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf",)

# ---------------------------------------------------------------------------
# MODULE P4 & P6: PERFORMANCE & OBSERVABILITY CONFIG (Phase P)
# ---------------------------------------------------------------------------
PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "True").lower() == "true"
RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
REDIS_CACHE_URL: str = os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/0")
CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "https://app.resumesphere.com,https://api.resumesphere.com").split(",")

# ---------------------------------------------------------------------------
# API Metadata & Environment Configuration
# ---------------------------------------------------------------------------

API_TITLE: str = "ResumeSphere AI"
API_VERSION: str = "15.0.0"
API_DESCRIPTION: str = (
    "Production AI Resume Analyzer & ATS Optimization Platform. "
    "Upload PDF resumes, score against ATS standards, extract skills, "
    "and compute dense semantic vector matches against target Job Descriptions."
)

APP_ENV: str = os.getenv("APP_ENV", "production")
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")
PORT: int = int(os.getenv("PORT", "8000"))

# Parse CORS Origins from environment variable (comma-separated or wildcard)
ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS: list[str] = [
    origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()
]

# ---------------------------------------------------------------------------
# Phase 3 & 4 — NLP Pipeline & Security Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = BASE_DIR.parent
DATASETS_DIR: Path = PROJECT_ROOT / "datasets"
SKILLS_CSV_PATH: Path = DATASETS_DIR / "skills.csv"

# Maximum upload size enforced by API endpoints (10 MB default)
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

# HuggingFace model identifier for sentence embeddings
EMBEDDING_MODEL_NAME: str = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)

