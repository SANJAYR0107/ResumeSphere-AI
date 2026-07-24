"""
job_readiness_service.py - Phase C Composite Job Readiness Score Service

Purpose
-------
Computes a comprehensive Job Readiness Index across Resume Quality, Interview Readiness,
Skill Readiness, Portfolio Readiness, and Communication Readiness.
"""

import logging
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class ReadinessCategoryBreakdown(TypedDict):
    category_name: str
    score_percentage: int
    status: str  # "Ready", "Moderate", "Needs Focus"
    feedback: str


class CompositeJobReadinessResult(TypedDict):
    overall_readiness_percentage: int
    readiness_level: str  # "Job Ready", "Near Ready", "Needs Preparation"
    category_breakdown: list[ReadinessCategoryBreakdown]
    weak_areas: list[str]
    improvement_plan: list[str]


def compute_job_readiness(
    ats_score: int = 75,
    interview_avg_score: float = 8.0,
    skill_match_percentage: int = 80,
    portfolio_score: float = 8.5
) -> CompositeJobReadinessResult:
    """Calculate multi-metric job readiness index and improvement plan."""
    resume_readiness = min(100, int(ats_score * 1.1))
    interview_readiness = min(100, int(interview_avg_score * 10))
    skill_readiness = skill_match_percentage
    portfolio_readiness = min(100, int(portfolio_score * 10))
    comm_readiness = min(100, int((interview_avg_score * 5) + 40))

    overall = int(round(
        (resume_readiness * 0.25) +
        (interview_readiness * 0.25) +
        (skill_readiness * 0.25) +
        (portfolio_readiness * 0.15) +
        (comm_readiness * 0.10)
    ))

    level = "Job Ready" if overall >= 80 else ("Near Ready" if overall >= 65 else "Needs Preparation")

    categories = [
        ReadinessCategoryBreakdown(
            category_name="Resume Quality",
            score_percentage=resume_readiness,
            status="Ready" if resume_readiness >= 75 else "Needs Focus",
            feedback=f"ATS score of {ats_score}/100 shows strong formatting and structure."
        ),
        ReadinessCategoryBreakdown(
            category_name="Interview Readiness",
            score_percentage=interview_readiness,
            status="Ready" if interview_readiness >= 75 else "Needs Focus",
            feedback=f"Interview average of {interview_avg_score}/10 demonstrates solid technical communication."
        ),
        ReadinessCategoryBreakdown(
            category_name="Skill Alignment",
            score_percentage=skill_readiness,
            status="Ready" if skill_readiness >= 75 else "Needs Focus",
            feedback=f"Skill match of {skill_match_percentage}% against target role requirements."
        ),
        ReadinessCategoryBreakdown(
            category_name="Portfolio & Projects",
            score_percentage=portfolio_readiness,
            status="Ready" if portfolio_readiness >= 75 else "Needs Focus",
            feedback="Projects demonstrate practical implementation."
        ),
        ReadinessCategoryBreakdown(
            category_name="Communication & Soft Skills",
            score_percentage=comm_readiness,
            status="Ready" if comm_readiness >= 75 else "Needs Focus",
            feedback="Clear verbal explanation structure."
        )
    ]

    weak_areas = [c["category_name"] for c in categories if c["score_percentage"] < 75]
    if not weak_areas:
        weak_areas = ["System Design Edge Cases"]

    plan = [
        f"Focus on improving {weak_areas[0]} by completing targeted practice sessions.",
        "Generate a tailored cover letter and apply to 5 target product companies weekly.",
        "Practice 1 mock interview session weekly on the Phase B AI platform."
    ]

    return CompositeJobReadinessResult(
        overall_readiness_percentage=min(100, overall),
        readiness_level=level,
        category_breakdown=categories,
        weak_areas=weak_areas,
        improvement_plan=plan
    )
