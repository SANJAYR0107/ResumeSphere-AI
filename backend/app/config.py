"""
config.py - Application Configuration

Central configuration module for the AI Resume Analyzer backend.
Defines constants and automatically creates required directories on startup.
"""

from pathlib import Path

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
ALLOWED_CONTENT_TYPE: str = "application/pdf"       # single value for equality checks
ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf",)

# ---------------------------------------------------------------------------
# API Metadata (used in main.py)
# ---------------------------------------------------------------------------

API_TITLE: str = "AI Resume Analyzer"
API_VERSION: str = "4.0.0"
API_DESCRIPTION: str = (
    "Phase 4 - ATS Scoring & AI-Powered Resume Analysis. "
    "Upload a PDF resume to receive ATS score, skill breakdown, "
    "job recommendations, improvement suggestions, and JD matching — "
    "powered by sentence-transformers and NLP."
)

# ---------------------------------------------------------------------------
# Phase 3 — NLP Pipeline Configuration
# ---------------------------------------------------------------------------

# Root of the project (two levels above backend/app/config.py)
PROJECT_ROOT: Path = BASE_DIR.parent

# Directory that holds all dataset files (e.g. skills.csv)
DATASETS_DIR: Path = PROJECT_ROOT / "datasets"

# Absolute path to the skills taxonomy CSV
SKILLS_CSV_PATH: Path = DATASETS_DIR / "skills.csv"

# Maximum upload size enforced by the /api/analyze endpoint (10 MB)
MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB

# HuggingFace model identifier for sentence embeddings
EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
