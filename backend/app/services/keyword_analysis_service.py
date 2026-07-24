"""
keyword_analysis_service.py - Phase 4 Keyword Analysis & Ranking Service

Purpose
-------
Performs granular keyword analysis comparing Resume against Job Description.
Categorizes keywords into Matched, Missing, Important Missing, and Extra Skills,
and ranks keywords by relevance and priority.
"""

import logging
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class RankedKeyword(TypedDict):
    keyword: str
    category: str
    importance: str  # "High", "Medium", "Low"
    score: int  # 0 to 100
    status: str  # "Matched", "Missing", "Extra"


class KeywordAnalysisResult(TypedDict):
    matched_keywords: list[str]
    missing_keywords: list[str]
    important_missing_keywords: list[str]
    extra_resume_skills: list[str]
    ranked_keywords: list[RankedKeyword]
    keyword_match_percentage: int


def analyze_keywords(
    resume_skills: list[str],
    jd_skills: list[str],
    jd_required_skills: list[str],
    resume_text: str,
    jd_text: str
) -> KeywordAnalysisResult:
    """Analyze and rank keyword alignment between Resume and Job Description."""
    resume_set = {s.strip().lower() for s in resume_skills}
    jd_set = {s.strip().lower() for s in jd_skills}
    req_set = {s.strip().lower() for s in jd_required_skills}

    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    important_missing_keywords: list[str] = []
    extra_resume_skills: list[str] = []
    ranked_keywords: list[RankedKeyword] = []

    # Map for original casing preservation
    original_casing: dict[str, str] = {}
    for s in resume_skills + jd_skills:
        original_casing[s.lower()] = s

    # 1. Evaluate JD Skills against Resume
    for s_lower in jd_set:
        orig = original_casing.get(s_lower, s_lower.title())
        is_required = s_lower in req_set
        importance = "High" if is_required else "Medium"
        score = 90 if is_required else 70

        if s_lower in resume_set or s_lower in resume_text.lower():
            matched_keywords.append(orig)
            ranked_keywords.append(RankedKeyword(
                keyword=orig,
                category="Skill",
                importance=importance,
                score=score,
                status="Matched"
            ))
        else:
            missing_keywords.append(orig)
            if is_required:
                important_missing_keywords.append(orig)
            ranked_keywords.append(RankedKeyword(
                keyword=orig,
                category="Skill",
                importance=importance,
                score=score,
                status="Missing"
            ))

    # 2. Identify Extra Resume Skills
    for s_lower in resume_set:
        orig = original_casing.get(s_lower, s_lower.title())
        if s_lower not in jd_set and s_lower not in jd_text.lower():
            extra_resume_skills.append(orig)
            ranked_keywords.append(RankedKeyword(
                keyword=orig,
                category="Value Add",
                importance="Low",
                score=40,
                status="Extra"
            ))

    # Sort ranked keywords by score descending
    ranked_keywords.sort(key=lambda k: (k["status"] != "Missing", k["score"]), reverse=True)

    match_percentage = min(100, int(round((len(matched_keywords) / len(jd_skills) * 100))) if jd_skills else 100)

    return KeywordAnalysisResult(
        matched_keywords=sorted(list(set(matched_keywords))),
        missing_keywords=sorted(list(set(missing_keywords))),
        important_missing_keywords=sorted(list(set(important_missing_keywords))),
        extra_resume_skills=sorted(list(set(extra_resume_skills))),
        ranked_keywords=ranked_keywords,
        keyword_match_percentage=match_percentage
    )
