"""
test_insights_service.py — Unit tests for insights_service.py
"""

from backend.app.services.insights_service import (
    analyze_projects,
    analyze_skills,
    analyze_experience,
    analyze_grammar,
    identify_strengths,
    identify_weaknesses,
    generate_actionable_suggestions
)


def test_analyze_projects():
    sections = {
        "projects": "Built a Python FastAPI backend that increased revenue by 20%. Uses Docker."}
    res = analyze_projects(sections)
    assert res["business_value_found"] is True
    assert res["technologies_mentioned"] >= 2
    assert res["missing_metrics"] is False


def test_analyze_skills():
    matches = [
        {"skill": "Python", "category": "Programming"},
        {"skill": "React", "category": "Frameworks"},
        {"skill": "Docker", "category": "Cloud"}
    ]
    res = analyze_skills(matches)
    assert "Programming" in res["groups"]
    assert "Python" in res["groups"]["Programming"]
    assert len(res["missing_skills"]) == 0


def test_analyze_experience():
    sections = {
        "experience": "Led a team in 2021 and 2022. Improved performance by 30%."}
    res = analyze_experience(sections)
    assert res["leadership_detected"] is True
    assert res["achievements_found"] == 4
    assert res["estimated_years"] == "1-2 years"


def test_analyze_grammar():
    quality_report = {"passive_language_found": ["was responsible for"]}
    res = analyze_grammar(
        "I was responsible for fixing the server!!!",
        quality_report)
    assert res["repeated_punctuation"] is True
    assert res["passive_voice_instances"] == 1


def test_identify_strengths_weaknesses():
    section_scores = {
        "technical_skills": {
            "score": 90}, "projects": {
            "score": 90}}
    qr = {"has_linkedin": True}
    strengths = identify_strengths(qr, section_scores)
    weaknesses = identify_weaknesses(qr, section_scores)
    assert "Strong Technical Skills" in strengths
    assert "Professional LinkedIn Linked" in strengths
    assert len(weaknesses) == 0


def test_generate_actionable_suggestions():
    qr = {"has_linkedin": False}
    scores = {"projects": {"score": 40}}
    suggestions = generate_actionable_suggestions(qr, scores)

    assert len(suggestions) > 0
    assert any("LinkedIn" in s["suggestion"] for s in suggestions)
