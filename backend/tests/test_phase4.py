from backend.app.services.ats_service import compute_ats_score
from backend.app.services.job_match_service import match_job_description
from backend.app.services.recommendation_service import get_job_recommendations
from backend.app.services.skill_gap_service import analyze_role_skill_gap


def test_ats_scoring_with_formatting():
    # Phase 4 introduced 'formatting' and rebalanced the rubric to 100.
    sections = {
        "summary": "Experienced engineer.",
        "experience": "Worked at Google for 5 years. " * 20,  # > 200 chars
        "education": "B.S. in Computer Science",
        "skills": "Python, Java",
        "projects": "Built a REST API",
        "certifications": "AWS Certified"
    }
    skills = ["Python", "Java", "Docker", "AWS", "FastAPI"]
    # Provide bullet points for formatting points
    raw_text = "• Summary\nExperienced engineer.\n• Experience\nWorked at Google."
    quality_report = {
        "grammar_issues": [],
        "passive_language_found": [],
        "weak_verbs_found": [],
        "has_linkedin": True,
        "missing_sections": []
    }
    result = compute_ats_score(sections, skills, raw_text, quality_report)

    # Verify new schema
    assert "formatting_grammar" in result["breakdown"]
    assert result["ats_score"] <= 100


def test_skill_gap_analysis():
    resume_skills = ["Python", "Java"]
    req_skills = ["AWS", "Docker", "Python"]
    pref_skills = ["Kubernetes"]

    result = analyze_role_skill_gap(resume_skills, req_skills, pref_skills)

    assert "overall_score" in result
    assert len(result["missing_skills"]) == 3  # AWS, Docker, Kubernetes
    assert "AWS" in result["critical_skills"]
    assert "Kubernetes" in result["nice_to_have_skills"]


from unittest.mock import patch

@patch("backend.app.services.job_match_service.get_embedding")
@patch("backend.app.services.job_match_service.get_raw_vector")
def test_job_match_service_structure(mock_get_raw, mock_get_embed):
    import numpy as np
    mock_get_raw.return_value = np.zeros(384)

    resume_text = "I am a software engineer with Python and Java."
    jd_text = "Looking for a software engineer with Python, AWS, and Docker."
    resume_skills = ["Python", "Java"]

    result = match_job_description(resume_text, jd_text, resume_skills)

    assert "match_score" in result
    assert "semantic_similarity" in result
    assert "Python" in result["matched_skills"]


def test_recommendation_service_structure():
    from backend.app.services.embedding_service import load_model
    load_model()

    resume_skills = ["Python", "FastAPI"]
    resume_text = "Backend developer."

    results = get_job_recommendations(resume_skills, resume_text)

    assert isinstance(results, list)
    assert len(results) <= 5
    if len(results) > 0:
        assert "title" in results[0]
        assert "match_score" in results[0]
