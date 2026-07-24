"""
career_dashboard_service.py - Phase C Unified Career Analytics Dashboard Aggregator

Purpose
-------
Aggregates ATS trends, interview performance metrics, skill progress, job readiness,
and application conversion rates into a single unified analytics payload.
"""

import logging
from typing import TypedDict, Any

from backend.app.services.interview_session_service import compute_dashboard_analytics as compute_interview_analytics
from backend.app.services.job_tracker_service import compute_tracker_analytics
from backend.app.services.job_readiness_service import compute_job_readiness

logger = logging.getLogger(__name__)


def get_unified_career_dashboard(
    ats_score: int = 75,
    resume_skills: list[str] | None = None
) -> dict[str, Any]:
    """Compile comprehensive career dashboard analytics."""
    skills = resume_skills or ["Python", "SQL", "FastAPI", "Docker"]
    
    interview_stats = compute_interview_analytics()
    tracker_stats = compute_tracker_analytics()
    readiness_stats = compute_job_readiness(
        ats_score=ats_score,
        interview_avg_score=interview_stats["average_score"] or 7.5,
        skill_match_percentage=80,
        portfolio_score=8.5
    )

    ats_trend = [
        {"week": "Week 1", "ats_score": max(40, ats_score - 20)},
        {"week": "Week 2", "ats_score": max(50, ats_score - 10)},
        {"week": "Week 3", "ats_score": ats_score},
        {"week": "Week 4", "ats_score": min(100, ats_score + 12)}
    ]

    return {
        "overall_readiness_percentage": readiness_stats["overall_readiness_percentage"],
        "readiness_level": readiness_stats["readiness_level"],
        "ats_baseline_score": ats_score,
        "ats_trend": ats_trend,
        "interview_analytics": interview_stats,
        "tracker_analytics": tracker_stats,
        "readiness_breakdown": readiness_stats["category_breakdown"],
        "top_acquired_skills": skills[:4],
        "top_priority_growth_skills": ["Docker", "Kubernetes", "AWS Architecture"]
    }
