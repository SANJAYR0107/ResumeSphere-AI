"""
test_ats_service.py — Unit tests for the Phase 4 ats_service.py
"""

from backend.app.services.ats_service import compute_ats_score


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_SECTIONS = {
    "summary": "Experienced engineer with 8 years in backend development.",
    "experience": (
        "Senior Software Engineer at TechCorp (2020–2024). "
        "Architected microservices with Python and FastAPI. "
        "Managed PostgreSQL databases on AWS. Led a team of 6 engineers "
        "and conducted 200+ code reviews. Implemented CI/CD with GitHub Actions."
    ),
    "education": "B.Tech Computer Science, XYZ University, 2018.",
    "skills": "Python, FastAPI, Docker, PostgreSQL, Redis, AWS, Kubernetes",
    "projects": "AI Resume Analyzer — FastAPI, PyMuPDF, sentence-transformers.",
    "certifications": "AWS Certified Solutions Architect — Associate (2022).",
}

FULL_TEXT = """
John Doe  john.doe@example.com  +1-555-0123  linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Experienced backend engineer with 8 years in backend development.

WORK EXPERIENCE
Senior Software Engineer at TechCorp (2020-2024).
Architected microservices with Python and FastAPI.
Managed PostgreSQL databases on AWS. Led a team of 6 engineers.
Increased performance by 40%. Spearheaded new deployments.

EDUCATION
B.Tech Computer Science, XYZ University, 2018.

TECHNICAL SKILLS
Python FastAPI Docker PostgreSQL Redis AWS Kubernetes Git Linux TypeScript

PROJECTS
AI Resume Analyzer - FastAPI, PyMuPDF, sentence-transformers. github.com/test

CERTIFICATIONS
AWS Certified Solutions Architect - Associate (2022).
"""

FULL_SKILLS = [
    "Python", "FastAPI", "Docker", "PostgreSQL", "Redis",
    "AWS", "Kubernetes", "Git", "Linux", "TypeScript",
]

EXPECTED_BREAKDOWN_KEYS = {
    "contact_info",
    "summary",
    "technical_skills",
    "experience",
    "projects",
    "education",
    "achievements",
    "action_verbs",
    "formatting_grammar",
    "external_links",
    "keyword_density",
    "resume_length"
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def ats(sections=None, skills=None, text="", qr=None):
    return compute_ats_score(
        sections=sections or {},
        skills=skills or [],
        raw_text=text,
        quality_report=qr or {}
    )


# ---------------------------------------------------------------------------
# Tests: Return structure
# ---------------------------------------------------------------------------

class TestReturnStructure:

    def test_returns_dict(self):
        result = ats()
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        result = ats()
        assert "ats_score" in result
        assert "ats_grade" in result
        assert "hiring_probability" in result
        assert "resume_strength_index" in result
        assert "recruiter_confidence" in result
        assert "breakdown" in result

    def test_breakdown_is_dict(self):
        result = ats()
        assert isinstance(result["breakdown"], dict)

    def test_all_breakdown_keys_present(self):
        result = ats(FULL_SECTIONS, FULL_SKILLS, FULL_TEXT)
        assert EXPECTED_BREAKDOWN_KEYS == set(result["breakdown"].keys())
        
    def test_breakdown_schema(self):
        result = ats(FULL_SECTIONS, FULL_SKILLS, FULL_TEXT)
        for key, value in result["breakdown"].items():
            assert "score" in value
            assert "weight" in value
            assert "reason" in value
            assert "improvement" in value


# ---------------------------------------------------------------------------
# Tests: Score range
# ---------------------------------------------------------------------------

class TestScoreRange:

    def test_empty_input_scores_zero_or_low(self):
        result = ats()
        # Even with empty, score could be non-zero due to things like empty text = 0 len score etc.
        # But generally should be very low.
        assert result["ats_score"] < 20

    def test_full_resume_scores_above_50(self):
        result = ats(FULL_SECTIONS, FULL_SKILLS, FULL_TEXT)
        assert result["ats_score"] >= 50

    def test_score_never_exceeds_100(self):
        big_skills = [f"Skill{i}" for i in range(100)]
        big_text = " ".join(["word"] * 600)
        result = ats(FULL_SECTIONS, big_skills, big_text)
        assert result["ats_score"] <= 100

    def test_score_is_non_negative(self):
        result = ats()
        assert result["ats_score"] >= 0


# ---------------------------------------------------------------------------
# Tests: Specific Categories
# ---------------------------------------------------------------------------

class TestSpecificCategories:

    def test_contact_info(self):
        res = ats(text="test@example.com +1234567890 linkedin.com")
        assert res["breakdown"]["contact_info"]["score"] >= 90

    def test_achievements_metrics(self):
        res = ats(text="Increased revenue by 50% and 3x performance")
        assert res["breakdown"]["achievements"]["score"] > 0

    def test_action_verbs(self):
        res = ats(text="Spearheaded and architected the optimized solution")
        assert res["breakdown"]["action_verbs"]["score"] > 0
        
    def test_external_links(self):
        res = ats(text="Check my github.com/test and my portfolio.dev")
        assert res["breakdown"]["external_links"]["score"] == 100
