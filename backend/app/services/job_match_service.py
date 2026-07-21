"""
job_match_service.py  —  Phase 4 Job Description Matching

Purpose
-------
Match a resume against a pasted job description using the existing
sentence-transformer embedding model.

Outputs
-------
``match_job_description`` → dict
    {match_score, matched_skills, missing_skills, jd_skills, semantic_similarity}
"""

import logging

import numpy as np

from backend.app.services.embedding_service import (
    get_embedding,
    get_raw_vector,
)
from backend.app.services.preprocessing_service import preprocess
from backend.app.services.skill_extractor_service import extract_skills

logger = logging.getLogger(__name__)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity between two 1-D numpy arrays."""
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def match_job_description(
    resume_text: str,
    jd_text: str,
    resume_skills: list[str],
) -> dict:
    """Match a resume against a job description.

    Computes a weighted score from semantic similarity (60 %) and skill
    keyword overlap (40 %).

    Parameters
    ----------
    resume_text : str
        Preprocessed resume text (output of ``preprocessing_service``).
    jd_text : str
        Raw job description text.  Preprocessing is applied internally.
    resume_skills : list[str]
        Canonical skill names extracted from the resume.

    Returns
    -------
    dict
        {
            "match_score"         : int,       # 0–100
            "matched_skills"      : list[str], # JD skills present in resume
            "missing_skills"      : list[str], # JD skills absent from resume
            "jd_skills"           : list[str], # all skills detected in JD
            "semantic_similarity" : float,     # 0.0 - 1.0
        }
    """
    # Preprocess the JD text
    clean_jd: str = preprocess(jd_text)

    # ── Semantic similarity ───────────────────────────────────────────────
    get_embedding(resume_text[:2000])
    resume_vec = get_raw_vector()
    resume_vec = resume_vec.copy() if resume_vec is not None else None

    get_embedding(clean_jd[:2000])
    jd_vec = get_raw_vector()

    semantic_sim: float = (
        _cosine_similarity(resume_vec, jd_vec)
        if resume_vec is not None and jd_vec is not None
        else 0.0
    )

    # ── Skill keyword overlap ─────────────────────────────────────────────
    jd_skills: list[str] = [s["skill"] for s in extract_skills(clean_jd)]
    resume_lower: set[str] = {s.lower() for s in resume_skills}
    jd_lower: set[str] = {s.lower() for s in jd_skills}

    matched_skills: list[str] = [
        s for s in jd_skills if s.lower() in resume_lower]
    missing_skills: list[str] = [
        s for s in jd_skills if s.lower() not in resume_lower]

    keyword_overlap: float = (
        len(matched_skills) / len(jd_skills) if jd_skills else 0.0
    )

    # ── Weighted composite score ──────────────────────────────────────────
    raw: float = semantic_sim * 0.6 + keyword_overlap * 0.4
    match_score: int = min(int(round(raw * 100)), 100)

    logger.info(
        "job_match_service: match_score=%d  semantic=%.3f  keyword=%.3f  "
        "matched=%d/%d skills",
        match_score,
        semantic_sim,
        keyword_overlap,
        len(matched_skills),
        len(jd_skills),
    )

    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "jd_skills": jd_skills,
        "semantic_similarity": semantic_sim,
    }
