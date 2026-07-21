from backend.app.services.ats_service import compute_ats_score
from backend.app.services.job_match_service import match_job_description
from backend.app.services.recommendation_service import get_job_recommendations
from backend.app.services.skill_gap_service import analyze_skill_gap


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
    matched = ["Python", "Java"]
    missing = ["AWS", "Docker", "Kubernetes"]

    result = analyze_skill_gap(matched, missing)

    assert result["matched_skills"] == matched
    assert result["missing_skills"] == missing
    assert "AWS" in result["recommended_skills"]
    assert len(result["learning_suggestions"]) > 0
    # Should recommend cloud certs for AWS/Docker
    assert any("cloud" in s.lower() for s in result["learning_suggestions"])


def test_job_match_service_structure():
    from backend.app.services.embedding_service import load_model
    load_model()

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
