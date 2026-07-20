"""
resume_pipeline.py  —  Phase 3 Resume Analysis Orchestration Pipeline

Purpose
-------
Orchestrate the complete NLP processing flow for a raw resume text string.
This is the **single entry point** that route handlers call after PDF
extraction.  It delegates every processing step to the appropriate service
and assembles the results into a unified ``ResumeAnalysis`` object.

Architecture position
---------------------
This module sits at the **Application / Use-Case layer** — above the
individual domain services (preprocessing, section detection, skill
extraction, embedding) but below the HTTP presentation layer (routes).

Flow
----
  raw_text (str)
       │
       ▼
  preprocessing_service.preprocess()      — unicode, bullets, whitespace
       │
       ▼
  section_service.detect_sections()       — split into labelled sections
       │
       ▼
  skill_extractor_service.extract_skills() — regex match against CSV taxonomy
       │
       ▼
  embedding_service.get_embedding()       — dense vector via MiniLM-L6-v2
       │
       ▼
  ResumeAnalysis (TypedDict)              — returned to caller

Inputs
------
raw_text    : str   — raw text from PyMuPDF extraction
filename    : str   — original filename (for logging/metadata)
page_count  : int   — total page count (passed through, not processed)

Outputs
-------
ResumeAnalysis (TypedDict)
  ``filename``           str              — original PDF filename
  ``pages``              int              — total page count
  ``candidate_name``     str              — best-guess first/last name
  ``sections``           dict[str, str]   — labelled section text
  ``skills``             list[str]        — matched skill names (sorted)
  ``skill_details``      list[SkillMatch] — skills with category + confidence
  ``skill_count``        int              — len(skills)
  ``embedding_dimension`` int             — 384 for MiniLM-L6-v2
  ``processing_time_ms`` int             — wall-clock time in milliseconds

Exceptions
----------
All service-level exceptions propagate upward.  The route handler is
responsible for catching them and mapping to appropriate HTTP status codes.

Candidate name heuristic
------------------------
The pipeline applies a simple heuristic to guess the candidate name:
it looks at the first 10 non-empty lines of the preprocessed text and
picks the first line that:
  - Is 2–5 words long
  - Contains only letters, spaces, hyphens, and apostrophes
  - Does not match any known section heading pattern
  - Is not an email address or phone number

This is not NER — it is a heuristic that works for the vast majority of
standard CV formats where the name appears at the top.

Complexity
----------
O(T) where T = character length of raw_text.  Each stage is a single
linear scan.  The only super-linear cost is the embedding model inference,
which is O(tokens²) internally but bounded by the model's 256-token limit.
"""

import logging
import re
import time
from typing import TypedDict

from backend.app.services.ats_service import compute_ats_score
from backend.app.services.embedding_service import EmbeddingResult, get_embedding
from backend.app.services.recommendation_service import get_job_recommendations
from backend.app.services.preprocessing_service import preprocess
from backend.app.services.section_service import detect_sections
from backend.app.services.skill_extractor_service import SkillMatch, extract_skills
from backend.app.services.suggestions_service import generate_suggestions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output Data Type
# ---------------------------------------------------------------------------

class ResumeAnalysis(TypedDict):
    """Complete structured output of the Phase 3 + 4 NLP pipeline."""
    # ── Phase 3 fields (unchanged) ──────────────────────────────────────
    filename: str
    pages: int
    candidate_name: str
    sections: dict[str, str]
    skills: list[str]
    skill_details: list[SkillMatch]
    skill_count: int
    embedding_dimension: int
    processing_time_ms: int
    clean_text: str
    # ── Phase 4 fields ──────────────────────────────────────────────────
    ats_score: int
    ats_breakdown: dict[str, int]
    suggestions: list[str]
    job_recommendations: list[dict]


# ---------------------------------------------------------------------------
# Internal: candidate name extraction heuristic
# ---------------------------------------------------------------------------

# Patterns that disqualify a line from being a candidate name
_RE_EMAIL: re.Pattern = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
_RE_PHONE: re.Pattern = re.compile(r"[\d\s\-\+\(\)]{7,}")
_RE_URL: re.Pattern = re.compile(r"https?://|www\.", re.IGNORECASE)
_RE_NAME_CHARS: re.Pattern = re.compile(r"^[A-Za-z][A-Za-z\s'\-\.]+$")

# Section heading keywords — a line with these words is likely a heading
_HEADING_DISQUALIFIERS: frozenset[str] = frozenset({
    "summary", "profile", "objective", "experience", "education", "skills",
    "projects", "certifications", "achievements", "languages", "resume",
    "curriculum", "vitae", "cv", "contact", "portfolio", "references",
    "about", "me", "internships", "volunteer", "publications",
})


def _extract_candidate_name(text: str) -> str:
    """Heuristically extract the candidate's name from resume text.

    Parameters
    ----------
    text : str
        Preprocessed resume text.

    Returns
    -------
    str
        Best-guess candidate name, or empty string if unable to determine.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Only inspect the first 15 lines — name is always near the top
    for line in lines[:15]:
        # Reject lines with emails, phones, or URLs
        if _RE_EMAIL.search(line):
            continue
        if _RE_PHONE.search(line):
            continue
        if _RE_URL.search(line):
            continue
        # Must be 2–5 words of purely alphabetic content
        words = line.split()
        if not (2 <= len(words) <= 5):
            continue
        if not _RE_NAME_CHARS.match(line):
            continue
        # Reject section headings
        if any(w.lower() in _HEADING_DISQUALIFIERS for w in words):
            continue
        # Looks like a name — return it title-cased for normalisation
        return line.title()

    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_pipeline(
    raw_text: str,
    filename: str,
    page_count: int,
) -> ResumeAnalysis:
    """Run the complete Phase 3 NLP analysis pipeline.

    Parameters
    ----------
    raw_text : str
        Raw text as returned by
        ``parser_service.extract_text_from_pdf``.
    filename : str
        Original name of the uploaded PDF file (used in metadata).
    page_count : int
        Total number of pages in the PDF (passed through unchanged).

    Returns
    -------
    ResumeAnalysis
        Fully populated analysis result ready for API serialisation.

    Raises
    ------
    RuntimeError
        If the embedding model has not been loaded via
        ``embedding_service.load_model()``.
    """
    t_start: float = time.perf_counter()
    logger.info("Pipeline START — file='%s', pages=%d", filename, page_count)

    # ── Stage 1: Preprocessing ────────────────────────────────────────────
    t0 = time.perf_counter()
    clean: str = preprocess(raw_text)
    logger.info(
        "Pipeline [1/4] Preprocessing complete — %d → %d chars  (%.1f ms)",
        len(raw_text),
        len(clean),
        (time.perf_counter() - t0) * 1000,
    )

    # ── Stage 2: Section detection ────────────────────────────────────────
    t0 = time.perf_counter()
    sections: dict[str, str] = detect_sections(clean)
    logger.info(
        "Pipeline [2/4] Sections detected — %d section(s)  (%.1f ms)",
        len(sections),
        (time.perf_counter() - t0) * 1000,
    )

    # ── Stage 3: Skill extraction ─────────────────────────────────────────
    t0 = time.perf_counter()
    skill_details: list[SkillMatch] = extract_skills(clean)
    skill_names: list[str] = [s["skill"] for s in skill_details]
    logger.info(
        "Pipeline [3/4] Skills extracted — %d skill(s)  (%.1f ms)",
        len(skill_names),
        (time.perf_counter() - t0) * 1000,
    )

    # ── Stage 4: Embedding generation ────────────────────────────────────
    # Use the first 2000 characters of cleaned text for the embedding.
    # This covers the most semantically dense part of the resume (summary,
    # skills, experience headline) while staying within the model's
    # token budget (~256 tokens ≈ 1000–1500 characters for English prose).
    t0 = time.perf_counter()
    embed_text: str = clean[:2000]
    embedding_result: EmbeddingResult = get_embedding(embed_text)
    logger.info(
        "Pipeline [4/4] Embedding generated — dim=%d  (%.1f ms)",
        embedding_result["dimension"],
        (time.perf_counter() - t0) * 1000,
    )

    # ── Stage 5: ATS scoring ──────────────────────────────────────────────
    t0 = time.perf_counter()
    ats_result: dict = compute_ats_score(
        sections=sections,
        skills=skill_names,
        raw_text=clean,
    )
    logger.info(
        "Pipeline [5/7] ATS score computed — score=%d  (%.1f ms)",
        ats_result["ats_score"],
        (time.perf_counter() - t0) * 1000,
    )

    # ── Stage 6: Suggestions ──────────────────────────────────────────────
    t0 = time.perf_counter()
    suggestions: list[str] = generate_suggestions(
        sections=sections,
        skills=skill_names,
        raw_text=clean,
        ats_breakdown=ats_result["breakdown"],
    )
    logger.info(
        "Pipeline [6/7] Suggestions generated — %d item(s)  (%.1f ms)",
        len(suggestions),
        (time.perf_counter() - t0) * 1000,
    )

    # ── Stage 7: Job recommendations ──────────────────────────────────────
    t0 = time.perf_counter()
    job_recs: list[dict] = get_job_recommendations(
        resume_skills=skill_names,
        resume_text=clean,
    )
    logger.info(
        "Pipeline [7/7] Job recommendations — %d result(s)  (%.1f ms)",
        len(job_recs),
        (time.perf_counter() - t0) * 1000,
    )

    # ── Candidate name heuristic ──────────────────────────────────────────
    candidate_name: str = _extract_candidate_name(clean)

    # ── Assemble result ───────────────────────────────────────────────────
    elapsed_ms: int = int((time.perf_counter() - t_start) * 1000)
    logger.info(
        "Pipeline COMPLETE — file='%s', skills=%d, sections=%d, ats=%d, "
        "embedding_dim=%d, total=%.0f ms",
        filename,
        len(skill_names),
        len(sections),
        ats_result["ats_score"],
        embedding_result["dimension"],
        elapsed_ms,
    )

    return ResumeAnalysis(
        filename=filename,
        pages=page_count,
        candidate_name=candidate_name,
        sections=sections,
        skills=skill_names,
        skill_details=skill_details,
        skill_count=len(skill_names),
        embedding_dimension=embedding_result["dimension"],
        processing_time_ms=elapsed_ms,
        clean_text=clean,
        ats_score=ats_result["ats_score"],
        ats_breakdown=ats_result["breakdown"],
        suggestions=suggestions,
        job_recommendations=job_recs,
    )
