"""
test_score_service.py — Unit tests for score_service.py
"""

from backend.app.services.score_service import calculate_section_scores, calculate_overall_score
from typing import Any


def test_calculate_section_scores():
    sections = {
        "experience": "A long string over 800 chars " * 30,
        "education": "BS in CS"}
    skills = ["Python", "Java", "Docker"]
    quality_report = {
        "grammar_issues": [],
        "passive_language_found": [],
        "weak_verbs_found": [],
        "has_linkedin": True,
        "missing_sections": []}
    ats_breakdown = {
        "formatting_grammar": {"score": 5},
        "keyword_density": {"score": 10},
        "contact_info": {"score": 10},
        "experience": {"score": 15},
        "skills": {"score": 15},
        "education": {"score": 10}
    }

    scores = calculate_section_scores(
        sections, skills, quality_report, ats_breakdown)

    assert scores["ats_score"]["score"] == 65
    assert scores["technical_skills"]["score"] == 15
    assert scores["projects"]["score"] == 0
    assert scores["experience"]["score"] == 100
    assert scores["education"]["score"] == 100
    assert scores["grammar"]["score"] == 100
    assert scores["formatting"]["score"] == 5
    assert scores["professionalism"]["score"] == 100
    assert scores["keyword"]["score"] == 10
    assert scores["completeness"]["score"] == 100


def test_calculate_overall_score():
    section_scores: dict[str, Any] = {
        "ats_score": {"score": 100, "reason": "ok", "improvement": "ok"},
        "experience": {"score": 100, "reason": "ok", "improvement": "ok"},
        "technical_skills": {"score": 100, "reason": "ok", "improvement": "ok"},
        "projects": {"score": 100, "reason": "ok", "improvement": "ok"},
        "completeness": {"score": 100, "reason": "ok", "improvement": "ok"},
        "grammar": {"score": 100, "reason": "ok", "improvement": "ok"},
        "formatting": {"score": 100, "reason": "ok", "improvement": "ok"},
        "professionalism": {"score": 100, "reason": "ok", "improvement": "ok"},
        "keyword": {"score": 100, "reason": "ok", "improvement": "ok"},
        "education": {"score": 100, "reason": "ok", "improvement": "ok"}
    }
    result = calculate_overall_score(section_scores)
    assert result["overall_score"] == 100
    assert result["explanation"].startswith("Outstanding")
