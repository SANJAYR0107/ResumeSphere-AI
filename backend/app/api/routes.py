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

from fastapi import APIRouter, File, HTTPException, UploadFile, Form, Response
from pydantic import BaseModel, Field
from typing import Any, Optional

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

from backend.app.services.jd_parser_service import parse_jd_text, parse_jd_file
from backend.app.services.keyword_analysis_service import analyze_keywords
from backend.app.services.ats_optimizer_service import analyze_sections_and_ats_optimization
from backend.app.services.resume_optimizer_service import (
    generate_rewrite_suggestions,
    simulate_ats_improvement,
    generate_interview_alignment,
    generate_learning_recommendations,
    generate_executive_summary,
)
from backend.app.services.report_service import generate_pdf_report
from backend.app.services.interview_generator_service import generate_interview_questions
from backend.app.services.interview_evaluator_service import evaluate_answer
from backend.app.services.interview_session_service import (
    create_interview_session,
    get_interview_session,
    submit_session_answer,
    list_interview_history,
    delete_interview_session,
    compute_dashboard_analytics,
)
from backend.app.services.coding_interview_service import execute_and_review_code
from backend.app.services.interview_report_service import generate_interview_pdf_report
from backend.app.services.career_coach_service import generate_career_roadmap
from backend.app.services.resume_chat_service import process_resume_chat_query
from backend.app.services.cover_letter_service import generate_cover_letter, generate_cover_letter_pdf
from backend.app.services.learning_roadmap_service import generate_learning_plan
from backend.app.services.certification_service import recommend_certifications
from backend.app.services.portfolio_analyzer_service import analyze_candidate_portfolio
from backend.app.services.job_readiness_service import compute_job_readiness
from backend.app.services.job_tracker_service import save_tracked_job, list_tracked_jobs, delete_tracked_job
from backend.app.services.career_dashboard_service import get_unified_career_dashboard

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


# ===========================================================================
# Phase 4 — Intelligent Resume vs Job Description Optimization Endpoints
# ===========================================================================

class OptimizeResumeRequest(BaseModel):
    resume_text: str
    job_description: str


class JdAnalysisRequest(BaseModel):
    resume_text: Optional[str] = None
    job_description: str


@router.post(
    "/jd-analysis",
    summary="Comprehensive Resume vs Job Description Optimization (Phase 4)",
    tags=["Resume vs JD Optimization"]
)
async def jd_analysis(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Form(None)
) -> dict[str, Any]:
    """Run full Phase 4 Resume vs Job Description Optimization Engine."""
    
    # 1. Parse Resume Text
    clean_resume_text = ""
    candidate_name = ""
    page_count = 1

    if resume_file:
        validate_pdf(resume_file)
        saved_path = save_uploaded_file(resume_file)
        extraction = extract_text_from_pdf(saved_path)
        clean_resume_text = clean_text(extraction["raw_text"])
        page_count = extraction["pages"]
    elif resume_text:
        clean_resume_text = clean_text(resume_text)

    if not clean_resume_text:
        raise HTTPException(status_code=400, detail="Please provide a valid PDF resume or resume_text.")

    # 2. Parse Job Description
    clean_jd_text = ""
    if jd_file:
        validate_pdf(jd_file)
        saved_jd_path = save_uploaded_file(jd_file)
        extraction_jd = extract_text_from_pdf(saved_jd_path)
        clean_jd_text = clean_text(extraction_jd["raw_text"])
    elif jd_text:
        clean_jd_text = clean_text(jd_text)

    if not clean_jd_text:
        raise HTTPException(status_code=400, detail="Please provide a valid Job Description text or PDF file.")

    # 3. Parse JD & Resume components
    parsed_jd = parse_jd_text(clean_jd_text)
    resume_sections = detect_sections(clean_resume_text)
    resume_skill_objs = extract_skills(clean_resume_text)
    resume_skills = [s["skill"] for s in resume_skill_objs]

    # Feature 1: Resume vs JD Match
    match_result = match_job_description(clean_resume_text, clean_jd_text, resume_skills)

    # Feature 2: Keyword Analysis
    keyword_analysis = analyze_keywords(
        resume_skills=resume_skills,
        jd_skills=parsed_jd["extracted_skills"],
        jd_required_skills=parsed_jd["required_skills"],
        resume_text=clean_resume_text,
        jd_text=clean_jd_text
    )

    # Feature 3 & 4: Section-wise Analysis & ATS Optimization Suggestions
    sec_analysis = analyze_sections_and_ats_optimization(
        resume_sections=resume_sections,
        resume_skills=resume_skills,
        jd_skills=parsed_jd["extracted_skills"],
        missing_skills=keyword_analysis["missing_keywords"],
        clean_text=clean_resume_text,
        jd_text=clean_jd_text
    )

    # Calculate ATS Score
    from backend.app.services.quality_service import analyze_quality
    qr = analyze_quality(clean_resume_text, resume_sections)
    ats_score_res = compute_ats_score(resume_sections, resume_skills, clean_resume_text, qr)
    current_ats = ats_score_res["ats_score"]

    # Feature 5: Resume Rewrite Suggestions
    rewrites = generate_rewrite_suggestions(
        candidate_name=candidate_name or "Candidate",
        role_title=parsed_jd["role_title"],
        resume_skills=resume_skills,
        missing_skills=keyword_analysis["missing_keywords"],
        yoe=parsed_jd["estimated_yoe"]
    )

    # Feature 8: ATS Improvement Simulator
    simulator = simulate_ats_improvement(
        current_ats_score=current_ats,
        missing_skills=keyword_analysis["important_missing_keywords"] or keyword_analysis["missing_keywords"]
    )

    # Feature 6: Interview Alignment
    interview_alignment = generate_interview_alignment(
        role_title=parsed_jd["role_title"],
        matched_skills=keyword_analysis["matched_keywords"],
        missing_skills=keyword_analysis["missing_keywords"]
    )

    # Feature 7: Learning Recommendations
    learning_recommendations = generate_learning_recommendations(
        missing_skills=keyword_analysis["missing_keywords"][:5]
    )

    # Feature 9: Executive Summary
    exec_summary = generate_executive_summary(
        match_score=match_result["match_score"],
        ats_score=current_ats,
        matched_skills=keyword_analysis["matched_keywords"],
        missing_skills=keyword_analysis["missing_keywords"],
        role_title=parsed_jd["role_title"]
    )

    # Composite Match Scores (Feature 1)
    ats_match_pct = int(round(match_result["match_score"] * 0.9 + (current_ats * 0.1)))
    overall_match_pct = int(round((match_result["match_score"] * 0.5) + (current_ats * 0.3) + (keyword_analysis["keyword_match_percentage"] * 0.2)))
    confidence_level = "High" if overall_match_pct >= 80 else ("Medium" if overall_match_pct >= 60 else "Low")

    return {
        "role_title": parsed_jd["role_title"],
        "match_scores": {
            "overall_match": min(100, overall_match_pct),
            "ats_match": min(100, ats_match_pct),
            "semantic_match": int(round(match_result["semantic_similarity"] * 100)),
            "keyword_match": keyword_analysis["keyword_match_percentage"],
            "confidence": confidence_level
        },
        "keyword_analysis": keyword_analysis,
        "section_analysis": sec_analysis["sections"],
        "ats_suggestions": sec_analysis["ats_suggestions"],
        "rewrite_suggestions": rewrites,
        "ats_simulator": simulator,
        "interview_alignment": interview_alignment,
        "learning_recommendations": learning_recommendations,
        "executive_summary": exec_summary,
        "clean_resume_text": clean_resume_text,
        "clean_jd_text": clean_jd_text
    }


@router.post(
    "/optimize-resume",
    summary="Generate targeted rewrite suggestions and ATS simulator",
    tags=["Resume vs JD Optimization"]
)
async def optimize_resume(request: OptimizeResumeRequest) -> dict[str, Any]:
    """Generate targeted rewrites and ATS score simulation for resume & JD."""
    clean_res = preprocess(request.resume_text)
    clean_jd = preprocess(request.job_description)

    parsed_jd = parse_jd_text(clean_jd)
    resume_skills = [s["skill"] for s in extract_skills(clean_res)]
    sections = detect_sections(clean_res)

    from backend.app.services.quality_service import analyze_quality
    qr = analyze_quality(clean_res, sections)
    ats_res = compute_ats_score(sections, resume_skills, clean_res, qr)

    kw_analysis = analyze_keywords(
        resume_skills=resume_skills,
        jd_skills=parsed_jd["extracted_skills"],
        jd_required_skills=parsed_jd["required_skills"],
        resume_text=clean_res,
        jd_text=clean_jd
    )

    rewrites = generate_rewrite_suggestions(
        candidate_name="",
        role_title=parsed_jd["role_title"],
        resume_skills=resume_skills,
        missing_skills=kw_analysis["missing_keywords"],
        yoe=parsed_jd["estimated_yoe"]
    )

    simulator = simulate_ats_improvement(
        current_ats_score=ats_res["ats_score"],
        missing_skills=kw_analysis["missing_keywords"]
    )

    return {
        "role_title": parsed_jd["role_title"],
        "rewrite_suggestions": rewrites,
        "ats_simulator": simulator
    }


@router.post(
    "/download-report",
    summary="Generate and download PDF optimization report (Feature 10)",
    tags=["Resume vs JD Optimization"]
)
async def download_report(request: dict[str, Any]) -> Response:
    """Generate a downloadable PDF optimization report."""
    try:
        # If payload contains raw resume & JD, run quick analysis first
        if "clean_resume_text" not in request and "resume_text" in request and "job_description" in request:
            clean_res = preprocess(request["resume_text"])
            clean_jd = preprocess(request["job_description"])
            parsed_jd = parse_jd_text(clean_jd)
            resume_skills = [s["skill"] for s in extract_skills(clean_res)]
            sections = detect_sections(clean_res)
            kw_analysis = analyze_keywords(resume_skills, parsed_jd["extracted_skills"], parsed_jd["required_skills"], clean_res, clean_jd)
            match_res = match_job_description(clean_res, clean_jd, resume_skills)
            from backend.app.services.quality_service import analyze_quality
            qr = analyze_quality(clean_res, sections)
            ats_res = compute_ats_score(sections, resume_skills, clean_res, qr)
            rewrites = generate_rewrite_suggestions("", parsed_jd["role_title"], resume_skills, kw_analysis["missing_keywords"], parsed_jd["estimated_yoe"])
            simulator = simulate_ats_improvement(ats_res["ats_score"], kw_analysis["missing_keywords"])
            interview = generate_interview_alignment(parsed_jd["role_title"], kw_analysis["matched_keywords"], kw_analysis["missing_keywords"])
            exec_sum = generate_executive_summary(match_res["match_score"], ats_res["ats_score"], kw_analysis["matched_keywords"], kw_analysis["missing_keywords"], parsed_jd["role_title"])
            sec_analysis = analyze_sections_and_ats_optimization(sections, resume_skills, parsed_jd["extracted_skills"], kw_analysis["missing_keywords"], clean_res, clean_jd)

            request = {
                "role_title": parsed_jd["role_title"],
                "match_scores": {
                    "overall_match": match_res["match_score"],
                    "ats_match": int(round(match_res["match_score"] * 0.9 + (ats_res["ats_score"] * 0.1))),
                    "semantic_match": int(round(match_res["semantic_similarity"] * 100)),
                    "keyword_match": kw_analysis["keyword_match_percentage"],
                    "confidence": "High" if match_res["match_score"] >= 80 else "Medium"
                },
                "keyword_analysis": kw_analysis,
                "ats_suggestions": sec_analysis["ats_suggestions"],
                "rewrite_suggestions": rewrites,
                "ats_simulator": simulator,
                "interview_alignment": interview,
                "executive_summary": exec_sum
            }

        pdf_bytes = generate_pdf_report(request)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="ResumeSphere_Optimization_Report.pdf"'
            }
        )
    except Exception as exc:
        logger.error("Failed to generate PDF report: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {exc}") from exc


# ===========================================================================
# Phase B — AI Interview Platform Endpoints (Modules B1 - B9)
# ===========================================================================

class StartInterviewSessionRequest(BaseModel):
    resume_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    interview_type: str = "Experienced"
    difficulty: str = "Medium"
    question_count: int = 5
    target_role: str = "Software Engineer"
    target_company: str = "Tech Corporation"


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    candidate_answer: str = ""
    time_spent_seconds: int = 45
    skip: bool = False


class CodeExecuteRequest(BaseModel):
    code_text: str
    language: str = "python"
    problem_title: str = "Two Sum"
    difficulty: str = "Easy"


@router.post(
    "/interview/session/start",
    summary="Start new interactive AI interview session (Module B1 & B2)",
    tags=["AI Interview Platform"]
)
async def start_interview_session(request: StartInterviewSessionRequest) -> dict[str, Any]:
    """Initialize new interactive interview session with personalized questions."""
    session = create_interview_session(
        resume_skills=request.resume_skills,
        missing_skills=request.missing_skills,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        question_count=request.question_count,
        target_role=request.target_role,
        target_company=request.target_company
    )
    return dict(session)


@router.get(
    "/interview/session/{session_id}",
    summary="Get active or saved interview session state (Module B2)",
    tags=["AI Interview Platform"]
)
async def get_session_state(session_id: str) -> dict[str, Any]:
    """Retrieve active or saved interview session status and progress."""
    session = get_interview_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Interview session '{session_id}' not found.")
    return dict(session)


@router.post(
    "/interview/session/submit-answer",
    summary="Evaluate candidate answer and generate dynamic follow-up (Module B3 & B4)",
    tags=["AI Interview Platform"]
)
async def submit_answer(request: SubmitAnswerRequest) -> dict[str, Any]:
    """Submit or skip a question answer, compute score out of 10, and generate dynamic follow-up."""
    try:
        res = submit_session_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            candidate_answer=request.candidate_answer,
            time_spent_seconds=request.time_spent_seconds,
            skip=request.skip
        )
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/interview/coding/execute",
    summary="Execute and review coding interview submission (Module B6)",
    tags=["AI Interview Platform"]
)
async def execute_coding_submission(request: CodeExecuteRequest) -> dict[str, Any]:
    """Evaluate candidate code submission with test cases, complexity analysis, and AI review."""
    review = execute_and_review_code(
        code_text=request.code_text,
        language=request.language,
        problem_title=request.problem_title,
        difficulty=request.difficulty
    )
    return dict(review)


@router.get(
    "/interview/history",
    summary="Retrieve interview session history (Module B8)",
    tags=["AI Interview Platform"]
)
async def get_interview_history() -> list[dict[str, Any]]:
    """Retrieve list of all past interview sessions."""
    return list_interview_history()


@router.delete(
    "/interview/history/{session_id}",
    summary="Delete past interview session (Module B8)",
    tags=["AI Interview Platform"]
)
async def delete_history_session(session_id: str) -> dict[str, Any]:
    """Delete an interview session from history."""
    success = delete_interview_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return {"status": "success", "deleted_session_id": session_id}


@router.get(
    "/interview/analytics",
    summary="Get aggregated interview dashboard analytics (Module B9)",
    tags=["AI Interview Platform"]
)
async def get_interview_analytics() -> dict[str, Any]:
    """Retrieve overall performance analytics across all sessions."""
    return compute_dashboard_analytics()


@router.post(
    "/interview/download-report",
    summary="Download PDF interview performance report (Module B5)",
    tags=["AI Interview Platform"]
)
async def download_interview_report(request: dict[str, Any]) -> Response:
    """Generate and stream downloadable PDF interview report."""
    try:
        session_id = request.get("session_id")
        fetched_session = get_interview_session(session_id) if session_id else None
        session_data: dict[str, Any] = dict(fetched_session) if fetched_session else request

        pdf_bytes = generate_interview_pdf_report(session_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="ResumeSphere_Interview_Report.pdf"'
            }
        )
    except Exception as exc:
        logger.error("Failed to generate PDF interview report: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF interview report: {exc}") from exc


# ===========================================================================
# Phase C — AI Career Assistant Endpoints (Modules C1 - C9)
# ===========================================================================

class CareerCoachRequest(BaseModel):
    resume_skills: list[str] = Field(default_factory=list)
    target_role: str = "Senior Software Engineer"


class ResumeChatRequest(BaseModel):
    query: str
    resume_skills: list[str] = Field(default_factory=list)
    ats_score: int = 75
    missing_skills: list[str] = Field(default_factory=list)
    target_role: str = "Software Engineer"


class CoverLetterRequest(BaseModel):
    candidate_name: str = "Jane Doe"
    target_role: str = "Software Engineer"
    company_name: str = "Tech Corporation"
    experience_type: str = "Experienced"
    resume_skills: list[str] = Field(default_factory=list)
    jd_text: str = ""


class LearningPlanRequest(BaseModel):
    target_skill: str = "Software Engineering"


class CertificationReq(BaseModel):
    resume_skills: list[str] = Field(default_factory=list)
    target_role: str = "Software Engineer"


class PortfolioReq(BaseModel):
    resume_skills: list[str] = Field(default_factory=list)
    project_text: str = ""


class JobReadinessReq(BaseModel):
    ats_score: int = 75
    interview_avg_score: float = 8.0
    skill_match_percentage: int = 80
    portfolio_score: float = 8.5


class TrackJobReq(BaseModel):
    company_name: str
    role_title: str
    location: str = "Remote"
    status: str = "Applied"
    salary_range: str = "$120K - $150K"
    notes: str = ""


@router.post(
    "/career/coach",
    summary="Generate 6-month AI career growth roadmap (Module C1)",
    tags=["AI Career Assistant"]
)
async def get_career_coach_roadmap(request: CareerCoachRequest) -> dict[str, Any]:
    """Generate 6-month career growth roadmap and skill priorities."""
    res = generate_career_roadmap(resume_skills=request.resume_skills, target_role=request.target_role)
    return dict(res)


@router.post(
    "/career/chat",
    summary="Contextual AI Resume Chat Assistant (Module C2)",
    tags=["AI Career Assistant"]
)
async def resume_chat(request: ResumeChatRequest) -> dict[str, Any]:
    """Process user query against resume, ATS, and interview context."""
    res = process_resume_chat_query(
        query=request.query,
        resume_skills=request.resume_skills,
        ats_score=request.ats_score,
        missing_skills=request.missing_skills,
        target_role=request.target_role
    )
    return dict(res)


@router.post(
    "/career/cover-letter/generate",
    summary="Generate tailored AI cover letter (Module C3)",
    tags=["AI Career Assistant"]
)
async def generate_cover_letter_endpoint(request: CoverLetterRequest) -> dict[str, Any]:
    """Generate professional cover letter tailored to candidate background and target company."""
    res = generate_cover_letter(
        candidate_name=request.candidate_name,
        target_role=request.target_role,
        company_name=request.company_name,
        experience_type=request.experience_type,
        resume_skills=request.resume_skills,
        jd_text=request.jd_text
    )
    return dict(res)


@router.post(
    "/career/cover-letter/download-pdf",
    summary="Download PDF cover letter (Module C3)",
    tags=["AI Career Assistant"]
)
async def download_cover_letter_pdf(request: dict[str, Any]) -> Response:
    """Generate and stream downloadable PDF cover letter."""
    try:
        pdf_bytes = generate_cover_letter_pdf(request)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="Cover_Letter.pdf"'
            }
        )
    except Exception as exc:
        logger.error("Failed to generate cover letter PDF: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter PDF: {exc}") from exc


@router.post(
    "/career/learning-roadmap",
    summary="Generate personalized learning plan (Module C4)",
    tags=["AI Career Assistant"]
)
async def get_learning_roadmap(request: LearningPlanRequest) -> dict[str, Any]:
    """Generate daily/weekly/monthly learning plan for a target skill."""
    res = generate_learning_plan(target_skill=request.target_skill)
    return dict(res)


@router.post(
    "/career/certifications",
    summary="Get ranked certification recommendations (Module C5)",
    tags=["AI Career Assistant"]
)
async def get_certifications(request: CertificationReq) -> list[dict[str, Any]]:
    """Rank certifications based on difficulty, career value, and candidate skills."""
    certs = recommend_certifications(resume_skills=request.resume_skills, target_role=request.target_role)
    return [dict(c) for c in certs]


@router.post(
    "/career/portfolio-analysis",
    summary="Analyze portfolio and GitHub project quality (Module C6)",
    tags=["AI Career Assistant"]
)
async def analyze_portfolio_endpoint(request: PortfolioReq) -> dict[str, Any]:
    """Analyze portfolio quality and suggest architecture & project ideas."""
    res = analyze_candidate_portfolio(resume_skills=request.resume_skills, project_text=request.project_text)
    return dict(res)


@router.post(
    "/career/job-readiness",
    summary="Calculate composite job readiness score (Module C7)",
    tags=["AI Career Assistant"]
)
async def get_job_readiness(request: JobReadinessReq) -> dict[str, Any]:
    """Compute overall job readiness score across Resume, Interview, Skill, and Portfolio."""
    res = compute_job_readiness(
        ats_score=request.ats_score,
        interview_avg_score=request.interview_avg_score,
        skill_match_percentage=request.skill_match_percentage,
        portfolio_score=request.portfolio_score
    )
    return dict(res)


@router.post(
    "/career/tracker/job",
    summary="Save tracked job application (Module C8)",
    tags=["AI Career Assistant"]
)
async def save_job_application(request: TrackJobReq) -> dict[str, Any]:
    """Track job application status."""
    entry = save_tracked_job(
        company_name=request.company_name,
        role_title=request.role_title,
        location=request.location,
        status=request.status,
        salary_range=request.salary_range,
        notes=request.notes
    )
    return dict(entry)


@router.get(
    "/career/tracker/jobs",
    summary="List all tracked job applications (Module C8)",
    tags=["AI Career Assistant"]
)
async def get_tracked_job_applications() -> list[dict[str, Any]]:
    """List tracked job applications."""
    jobs = list_tracked_jobs()
    return [dict(j) for j in jobs]


@router.delete(
    "/career/tracker/job/{job_id}",
    summary="Delete tracked job application (Module C8)",
    tags=["AI Career Assistant"]
)
async def delete_job_application(job_id: str) -> dict[str, Any]:
    """Delete a tracked job entry."""
    success = delete_tracked_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job entry '{job_id}' not found.")
    return {"status": "success", "deleted_job_id": job_id}


@router.get(
    "/career/dashboard",
    summary="Get unified Phase C career analytics dashboard (Module C9)",
    tags=["AI Career Assistant"]
)
async def get_career_dashboard_endpoint(ats_score: int = 75) -> dict[str, Any]:
    """Retrieve overall career metrics across ATS, interviews, readiness, and job applications."""
    return get_unified_career_dashboard(ats_score=ats_score)



