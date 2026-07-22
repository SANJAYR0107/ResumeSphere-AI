"""
routes.py - API Route Definitions (Phase 2 + Phase 3)

Presentation layer: receives HTTP requests, validates inputs, delegates all
business logic to the service/pipeline layer, and formats HTTP responses.

Endpoint summary:
  POST /api/upload   →  UploadResponse   (Phase 2 — unchanged)
  POST /api/analyze  →  AnalyzeResponse  (Phase 3 — NLP pipeline)
"""

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from typing import Any

from backend.app.config import MAX_UPLOAD_BYTES
from backend.app.services.job_match_service import match_job_description
from backend.app.services.parser_service import (
    clean_text,
    extract_text_from_pdf,
    save_uploaded_file,
    validate_pdf,
)
from backend.app.services.preprocessing_service import preprocess
from backend.app.services.skill_extractor_service import extract_skills
from backend.resume_pipeline import ResumeAnalysis, run_pipeline
from backend.app.services.ats_service import compute_ats_score, AtsCategoryBreakdown
from backend.app.services.section_service import detect_sections
from backend.app.services.recommendation_service import get_job_recommendations
from backend.app.services.skill_gap_service import analyze_skill_gap
from backend.app.services.recruiter_service import generate_recruiter_insights

# Module-level logger
logger = logging.getLogger(__name__)

# Number of characters to include in the public-facing text preview.
# The full cleaned text is retained in memory for downstream NLP (Phase 3+).
PREVIEW_LENGTH: int = 300

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

# All routes defined here are mounted under the /api prefix in main.py
router = APIRouter(prefix="/api", tags=["Resume Upload"])


# ---------------------------------------------------------------------------
# Response Schema
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    """Structured JSON response returned after a successful PDF upload.

    The ``preview`` field is intentionally limited to the first
    ``PREVIEW_LENGTH`` characters of the cleaned text.  The full extracted
    text is kept in-process for Phase 3 NLP preprocessing and is never
    returned directly to the client (to avoid leaking PII such as phone
    numbers, home addresses, and email addresses).

    Attributes
    ----------
    filename : str
        Original filename of the uploaded resume.
    pages : int
        Total number of pages detected in the PDF document.
    characters : int
        Total character count of the *full* cleaned text.
    preview : str
        First ``PREVIEW_LENGTH`` characters of the cleaned text.
    """

    filename: str
    pages: int
    characters: int
    preview: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a PDF resume",
    description=(
        "Accepts a PDF resume via multipart/form-data, extracts all readable "
        "text using PyMuPDF, and returns metadata plus a short text preview. "
        "The full text is retained internally for NLP processing (Phase 3)."
    ),
    responses={
        200: {"description": "Text extracted successfully."},
        400: {"description": "Uploaded file is not a valid PDF."},
        404: {"description": "The PDF could not be read or is corrupt."},
        500: {"description": "Unexpected server error during processing."},
    },
)
async def upload_resume(
    resume: UploadFile = File(
        ...,
        description="PDF resume file to be uploaded and parsed.",
    ),
) -> UploadResponse:
    """Handle a PDF resume upload and return a text preview.

    Processing pipeline:
      1. **validate_pdf** – Rejects non-PDF files with HTTP 400.
      2. **save_uploaded_file** – Streams the upload to the uploads/ folder.
      3. **extract_text_from_pdf** – Opens the saved PDF with PyMuPDF and
         collects raw text from every page.
      4. **clean_text** – Normalises whitespace for clean output.
      5. Stores the full cleaned text internally (available for Phase 3 NLP).
      6. Returns :class:`UploadResponse` with filename, page count,
         total character count, and a ``PREVIEW_LENGTH``-character preview.

    Parameters
    ----------
    resume : UploadFile
        The PDF file received via the ``resume`` multipart field.

    Returns
    -------
    UploadResponse
        JSON object containing ``filename``, ``pages``, ``characters``,
        and ``preview`` (first 300 characters of the extracted text).

    Raises
    ------
    HTTPException (400)
        If the uploaded file is not a PDF.
    HTTPException (404)
        If the saved PDF file cannot be opened/read.
    HTTPException (500)
        For any unexpected error during processing.
    """
    # ── Step 1: Validate that the upload is a PDF ───────────────────────────
    validate_pdf(resume)

    # ── Step 2: Persist the file to disk ────────────────────────────────────
    saved_path: Path = save_uploaded_file(resume)

    # ── Step 3: Extract raw text and page count from the PDF ────────────────
    import time
    t0 = time.perf_counter()
    extraction_result: dict = extract_text_from_pdf(saved_path)
    raw_text: str = extraction_result["raw_text"]
    page_count: int = extraction_result["pages"]
    logger.info("Parser time: %.1f ms", (time.perf_counter() - t0) * 1000)

    # ── Step 4: Clean the extracted text ────────────────────────────────────
    cleaned_text: str = clean_text(raw_text)
    # The full cleaned_text is intentionally kept here in-process.
    # Phase 3 NLP preprocessing (tokenization, lemmatization, etc.) will
    # consume it directly without re-reading from disk.

    # ── Step 5: Slice a safe public preview ─────────────────────────────────
    preview: str = cleaned_text[:PREVIEW_LENGTH]

    logger.info(
        "Resume '%s' processed: %d page(s), %d character(s) total, preview=%d chars.",
        resume.filename,
        page_count,
        len(cleaned_text),
        len(preview),
    )

    # ── Step 6: Build and return the structured response ────────────────────
    return UploadResponse(
        filename=resume.filename or "unknown.pdf",
        pages=page_count,
        characters=len(cleaned_text),   # total chars of the full cleaned text
        preview=preview,                # only the first 300 chars are returned
    )


# ===========================================================================
# Phase 3 — NLP Analysis Endpoint
# ===========================================================================


class SkillDetail(BaseModel):
    """Single matched skill entry with taxonomy metadata.

    Attributes
    ----------
    skill : str
        Canonical skill name as defined in skills.csv.
    category : str
        Taxonomy category (e.g. Programming, Cloud, AI/ML).
    confidence : float
        Normalised occurrence score in [0.0, 1.0].  A higher value means
        the skill appears more frequently relative to other matched skills.
    """

    skill: str
    category: str
    confidence: float = Field(ge=0.0, le=1.0)


class JobRecommendationSchema(BaseModel):
    """A single job recommendation entry."""

    title: str
    match_score: int = Field(ge=0, le=100)
    description: str
    matched_skills: list[str]


class AnalyzeResponse(BaseModel):
    """Structured JSON response returned by POST /api/analyze.

    Attributes
    ----------
    filename : str
        Original filename of the uploaded resume.
    pages : int
        Total number of pages in the PDF.
    candidate_name : str
        Best-guess candidate name extracted from the top of the resume.
        Empty string if the heuristic could not determine a name.
    sections : dict[str, str]
        Resume sections detected and labelled (e.g. summary, experience,
        education, skills).  Keys are canonical section names.
    skills : list[str]
        Alphabetically sorted list of matched skill names.
    skill_details : list[SkillDetail]
        Full skill matches including category and confidence score.
    skill_count : int
        Total number of unique skills detected.
    embedding_dimension : int
        Dimensionality of the generated sentence embedding (384 for
        all-MiniLM-L6-v2).  The raw vector is NOT returned in this response.
    processing_time_ms : int
        Total wall-clock processing time for the NLP pipeline in milliseconds.
    clean_text : str
        Preprocessed resume text (used by the frontend for JD matching).
    ats_score : int
        Overall ATS compatibility score (0–100).
    ats_breakdown : dict[str, int]
        Per-category score breakdown (nine categories).
    suggestions : list[str]
        Ordered list of actionable resume-improvement suggestions.
    job_recommendations : list[JobRecommendationSchema]
        Top-5 job recommendations ranked by semantic + skill similarity.
    """

    filename: str
    pages: int
    candidate_name: str
    sections: dict[str, str]
    skills: list[str]
    skill_details: list[SkillDetail]
    skill_count: int
    embedding_dimension: int
    processing_time_ms: int
    clean_text: str
    ats_score: int = Field(ge=0, le=100)
    ats_breakdown: dict[str, AtsCategoryBreakdown]
    ats_grade: str
    hiring_probability: str
    resume_strength_index: float
    recruiter_confidence: str
    suggestions: list[str]
    job_recommendations: list[JobRecommendationSchema]
    quality_report: Any
    # ── Phase 2 fields ──────────────────────────────────────────────────
    overall_score: Any
    section_scores: Any
    project_analysis: Any
    skill_analysis: Any
    experience_analysis: Any
    grammar_analysis: Any
    keyword_analysis: Any
    summary_analysis: Any
    strengths: list[str]
    weaknesses: list[str]
    actionable_suggestions: list[Any]
    recruiter_summary: Any
    career_insights: Any
    interview_readiness: Any
    # ── Phase 3 fields ──────────────────────────────────────────────────
    recommended_jobs: Any = None
    skill_gap: Any = None
    career_roadmap: Any = None
    interview_preparation: Any = None


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze a PDF resume (Phase 3 NLP Pipeline)",
    description=(
        "Accepts a PDF resume via multipart/form-data and runs the full "
        "Phase 3 NLP pipeline: text extraction, preprocessing, section "
        "detection, skill extraction, and sentence embedding generation. "
        "Returns structured semantic information ready for ATS scoring "
        "and job recommendation (Phase 4+)."
    ),
    responses={
        200: {"description": "NLP analysis completed successfully."},
        400: {"description": "Uploaded file is not a valid PDF."},
        413: {"description": "File exceeds the 10 MB size limit."},
        404: {"description": "The PDF could not be read or is corrupt."},
        500: {"description": "Unexpected server error during NLP processing."},
    },
    tags=["Resume Analysis"],
)
async def analyze_resume(
    resume: UploadFile = File(
        ...,
        description="PDF resume file to be uploaded and analysed (max 10 MB).",
    ),
) -> AnalyzeResponse:
    """Receive a PDF resume and return structured NLP analysis.

    Processing pipeline:
      1. **File size check** — Rejects uploads > 10 MB with HTTP 413.
      2. **validate_pdf** — Rejects non-PDF files with HTTP 400.
      3. **save_uploaded_file** — Streams the upload to the uploads/ folder.
      4. **extract_text_from_pdf** — Extracts raw text via PyMuPDF.
      5. **run_pipeline** — Runs the Phase 3 NLP pipeline:
           a. preprocessing_service.preprocess()
           b. section_service.detect_sections()
           c. skill_extractor_service.extract_skills()
           d. embedding_service.get_embedding()
      6. Returns :class:`AnalyzeResponse` with full structured output.

    Parameters
    ----------
    resume : UploadFile
        The PDF file received via the ``resume`` multipart field.

    Returns
    -------
    AnalyzeResponse
        JSON object with filename, pages, candidate_name, sections,
        skills, skill_details, skill_count, embedding_dimension,
        and processing_time_ms.

    Raises
    ------
    HTTPException (400)
        If the uploaded file is not a PDF.
    HTTPException (413)
        If the uploaded file exceeds MAX_UPLOAD_BYTES (10 MB).
    HTTPException (404)
        If the saved PDF file cannot be opened/read.
    HTTPException (500)
        For any unexpected error during NLP processing.
    """
    # ── Step 1: Enforce file size limit ────────────────────────────────────
    # Read all bytes up-front so we can check size before saving to disk.
    # MAX_UPLOAD_BYTES = 10 MB as defined in config.py.
    content: bytes = await resume.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File '{resume.filename}' is {len(content):,} bytes, "
                f"which exceeds the 10 MB limit ({MAX_UPLOAD_BYTES:,} bytes)."
            ),
        )
    # Rewind the file so downstream functions can re-read it
    await resume.seek(0)

    # ── Step 2: Validate MIME type and extension ────────────────────────────
    validate_pdf(resume)

    # ── Step 3: Persist to disk ─────────────────────────────────────────────
    saved_path: Path = save_uploaded_file(resume)

    # ── Step 4: Extract raw text via PyMuPDF ───────────────────────────────
    import time
    t0 = time.perf_counter()
    extraction: dict = extract_text_from_pdf(saved_path)
    raw_text: str = extraction["raw_text"]
    page_count: int = extraction["pages"]
    logger.info("Parser time: %.1f ms", (time.perf_counter() - t0) * 1000)

    # ── Step 5: Run NLP pipeline ────────────────────────────────────────────
    try:
        analysis: ResumeAnalysis = run_pipeline(
            raw_text=raw_text,
            filename=resume.filename or "resume.pdf",
            page_count=page_count,
        )
    except RuntimeError as exc:
        logger.error("Pipeline error for '%s': %s", resume.filename, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Unexpected pipeline error for '%s': %s",
            resume.filename,
            exc)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during NLP analysis: {exc}",
        ) from exc

    # Generate Recruiter Insights based on the pipeline output
    recruiter_data = generate_recruiter_insights(
        ats_score=analysis["ats_score"],
        skills=analysis["skills"],
        experience_text=analysis["sections"].get("experience", ""),
        projects_text=analysis["sections"].get("projects", "")
    )

    # ── Step 6: Build and return the structured response ──────────────────
    return AnalyzeResponse(
        filename=analysis["filename"],
        pages=analysis["pages"],
        candidate_name=analysis["candidate_name"],
        sections=analysis["sections"],
        skills=analysis["skills"],
        skill_details=[
            SkillDetail(
                skill=s["skill"],
                category=s["category"],
                confidence=s["confidence"],
            )
            for s in analysis["skill_details"]
        ],
        skill_count=analysis["skill_count"],
        embedding_dimension=analysis["embedding_dimension"],
        processing_time_ms=analysis["processing_time_ms"],
        clean_text=analysis["clean_text"],
        ats_score=analysis["ats_score"],
        ats_breakdown=analysis["ats_breakdown"],
        ats_grade=analysis.get("ats_grade", "N/A"),
        hiring_probability=analysis.get("hiring_probability", "N/A"),
        resume_strength_index=analysis.get("resume_strength_index", 0.0),
        recruiter_confidence=analysis.get("recruiter_confidence", "N/A"),
        suggestions=analysis["suggestions"],
        job_recommendations=[
            JobRecommendationSchema(
                title=r["title"],
                match_score=r["match_score"],
                description=r["description"],
                matched_skills=r["matched_skills"],
            )
            for r in analysis["job_recommendations"]
        ],
        quality_report=analysis["quality_report"],
        overall_score=analysis["overall_score"],
        section_scores=analysis["section_scores"],
        project_analysis=analysis["project_analysis"],
        skill_analysis=analysis["skill_analysis"],
        experience_analysis=analysis["experience_analysis"],
        grammar_analysis=analysis["grammar_analysis"],
        keyword_analysis=analysis["keyword_analysis"],
        summary_analysis=analysis["summary_analysis"],
        strengths=analysis["strengths"],
        weaknesses=analysis["weaknesses"],
        actionable_suggestions=analysis["actionable_suggestions"],
        recruiter_summary=recruiter_data["recruiter_summary"],
        career_insights=recruiter_data["career_insights"],
        interview_readiness=recruiter_data["interview_readiness"],
        recommended_jobs=analysis.get("recommended_jobs"),
        skill_gap=analysis.get("skill_gap"),
        career_roadmap=analysis.get("career_roadmap"),
        interview_preparation=analysis.get("interview_preparation")
    )


# ===========================================================================
# Phase 4 — Job Description Matching Endpoint
# ===========================================================================


class JobMatchRequest(BaseModel):
    """Request body for POST /api/job-match."""

    resume_text: str = Field(
        ...,
        description="Preprocessed resume text (from a prior /api/analyze call).",
    )
    job_description: str = Field(
        ...,
        min_length=20,
        description="Raw job description text pasted by the user.",
    )


class JobMatchResponse(BaseModel):
    """Response for POST /api/job-match."""

    match_score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    jd_skills: list[str]
    semantic_similarity: float = Field(ge=0.0, le=1.0)


@router.post(
    "/job-match",
    response_model=JobMatchResponse,
    summary="Match resume against a job description (Phase 4)",
    description=(
        "Accepts preprocessed resume text and a job description, then computes "
        "a semantic + keyword match score using the existing embedding model. "
        "Returns the composite match score, matched skills, and missing skills."
    ),
    responses={
        200: {"description": "Match computed successfully."},
        400: {"description": "Job description is too short or invalid."},
        500: {"description": "Embedding model not loaded or unexpected error."},
    },
    tags=["Resume Analysis"],
)
async def job_match(
    request: JobMatchRequest,
) -> JobMatchResponse:
    """Compute semantic + keyword match between a resume and a job description.

    Parameters
    ----------
    request : JobMatchRequest
        JSON body with ``resume_text`` and ``job_description``.

    Returns
    -------
    JobMatchResponse
        ``match_score`` (0–100), ``matched_skills``, ``missing_skills``,
        and ``jd_skills``.

    Raises
    ------
    HTTPException (500)
        If the embedding model is not loaded or an unexpected error occurs.
    """
    # Extract skills from the resume text for overlap computation
    clean_resume: str = preprocess(request.resume_text)
    resume_skill_matches = extract_skills(clean_resume)
    resume_skills: list[str] = [s["skill"] for s in resume_skill_matches]

    try:
        result = match_job_description(
            resume_text=clean_resume,
            jd_text=request.job_description,
            resume_skills=resume_skills,
        )
    except RuntimeError as exc:
        logger.error("job-match endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("job-match unexpected error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during JD matching: {exc}",
        ) from exc

    return JobMatchResponse(
        match_score=result["match_score"],
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
        jd_skills=result["jd_skills"],
        semantic_similarity=result["semantic_similarity"],
    )


class SkillGapRequest(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]


class SkillGapResponse(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    recommended_skills: list[str]
    learning_suggestions: list[str]


@router.post("/skill-gap",
             response_model=SkillGapResponse,
             tags=["Resume Analysis"])
async def skill_gap(request: SkillGapRequest) -> SkillGapResponse:
    result = analyze_skill_gap(request.matched_skills, request.missing_skills)
    return SkillGapResponse(**result)


class RecommendationsRequest(BaseModel):
    resume_skills: list[str]
    resume_text: str


class RecommendationsResponse(BaseModel):
    recommendations: list[JobRecommendationSchema]


@router.post("/recommendations",
             response_model=RecommendationsResponse,
             tags=["Resume Analysis"])
async def recommendations(
        request: RecommendationsRequest) -> RecommendationsResponse:
    clean_resume = preprocess(request.resume_text)
    recs = get_job_recommendations(request.resume_skills, clean_resume)
    return RecommendationsResponse(
        recommendations=[JobRecommendationSchema(**r) for r in recs]
    )


class AtsScoreRequest(BaseModel):
    resume_text: str


class AtsScoreResponse(BaseModel):
    ats_score: int
    ats_grade: str
    hiring_probability: str
    resume_strength_index: float
    recruiter_confidence: str
    breakdown: dict[str, AtsCategoryBreakdown]


@router.post("/ats-score",
             response_model=AtsScoreResponse,
             tags=["Resume Analysis"])
async def ats_score(request: AtsScoreRequest) -> AtsScoreResponse:
    clean_resume = preprocess(request.resume_text)
    sections = detect_sections(clean_resume)
    skills_matches = extract_skills(clean_resume)
    skills = [s["skill"] for s in skills_matches]
    # quality_report is needed for the new ats scoring.
    # In a lightweight ats_score endpoint, we can pass a dummy or run the basic quality check.
    from backend.app.services.quality_service import analyze_quality
    qr = analyze_quality(clean_resume, sections)
    
    result = compute_ats_score(sections, skills, clean_resume, qr)
    return AtsScoreResponse(
        ats_score=result["ats_score"],
        ats_grade=result["ats_grade"],
        hiring_probability=result["hiring_probability"],
        resume_strength_index=result["resume_strength_index"],
        recruiter_confidence=result["recruiter_confidence"],
        breakdown=result["breakdown"]
    )
