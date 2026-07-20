"""
test_ats_service.py — Unit tests for ats_service.py

Test matrix covers:
  - Empty input scores zero
  - Full resume scores above threshold
  - Breakdown sums to ats_score
  - All expected breakdown keys present
  - Individual rubric categories (contact, summary, skills, etc.)
  - Edge cases (no sections, many skills, zero word count)
"""

import pytest

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

EDUCATION
B.Tech Computer Science, XYZ University, 2018.

TECHNICAL SKILLS
Python FastAPI Docker PostgreSQL Redis AWS Kubernetes Git Linux TypeScript

PROJECTS
AI Resume Analyzer - FastAPI, PyMuPDF, sentence-transformers.

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
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "resume_length",
    "keyword_density",
    "formatting",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def ats(sections=None, skills=None, text=""):
    return compute_ats_score(
        sections=sections or {},
        skills=skills or [],
        raw_text=text,
    )


# ---------------------------------------------------------------------------
# Tests: Return structure
# ---------------------------------------------------------------------------

class TestReturnStructure:

    def test_returns_dict(self):
        result = ats()
        assert isinstance(result, dict)

    def test_has_ats_score_key(self):
        result = ats()
        assert "ats_score" in result

    def test_has_breakdown_key(self):
        result = ats()
        assert "breakdown" in result

    def test_breakdown_is_dict(self):
        result = ats()
        assert isinstance(result["breakdown"], dict)

    def test_all_breakdown_keys_present(self):
        result = ats(FULL_SECTIONS, FULL_SKILLS, FULL_TEXT)
        assert EXPECTED_BREAKDOWN_KEYS == set(result["breakdown"].keys())

    def test_ats_score_equals_sum_of_breakdown(self):
        result = ats(FULL_SECTIONS, FULL_SKILLS, FULL_TEXT)
        assert result["ats_score"] == sum(result["breakdown"].values())

    def test_ats_score_is_int(self):
        result = ats(FULL_SECTIONS, FULL_SKILLS, FULL_TEXT)
        assert isinstance(result["ats_score"], int)


# ---------------------------------------------------------------------------
# Tests: Score range
# ---------------------------------------------------------------------------

class TestScoreRange:

    def test_empty_input_scores_zero(self):
        result = ats()
        assert result["ats_score"] == 0

    def test_full_resume_scores_above_60(self):
        result = ats(FULL_SECTIONS, FULL_SKILLS, FULL_TEXT)
        assert result["ats_score"] > 60

    def test_score_never_exceeds_100(self):
        # Even with very long text and many skills it should not exceed 100
        big_skills = [f"Skill{i}" for i in range(100)]
        big_text = " ".join(["word"] * 600)
        result = ats(FULL_SECTIONS, big_skills, big_text)
        assert result["ats_score"] <= 100

    def test_score_is_non_negative(self):
        result = ats()
        assert result["ats_score"] >= 0


# ---------------------------------------------------------------------------
# Tests: Contact information (10 pts)
# ---------------------------------------------------------------------------

class TestContactInfo:

    def test_email_adds_contact_points(self):
        result_with = ats(text="jane@example.com")
        result_without = ats(text="Jane Doe, Software Engineer")
        assert result_with["breakdown"]["contact_info"] > result_without["breakdown"]["contact_info"]

    def test_no_contact_scores_zero(self):
        result = ats(text="Jane Doe Software Engineer Python Developer")
        assert result["breakdown"]["contact_info"] == 0

    def test_all_contact_info_scores_ten(self):
        text = "john@example.com  +1-555-0123  linkedin.com/in/john"
        result = ats(text=text)
        assert result["breakdown"]["contact_info"] == 10


# ---------------------------------------------------------------------------
# Tests: Summary (10 pts)
# ---------------------------------------------------------------------------

class TestSummarySection:

    def test_summary_present_scores_ten(self):
        result = ats(sections={"summary": "Senior engineer with 8 years."})
        assert result["breakdown"]["summary"] == 10

    def test_no_summary_scores_zero(self):
        result = ats(sections={"experience": "Worked at TechCorp."})
        assert result["breakdown"]["summary"] == 0


# ---------------------------------------------------------------------------
# Tests: Experience (20 pts)
# ---------------------------------------------------------------------------

class TestExperienceSection:

    def test_no_experience_scores_zero(self):
        result = ats(sections={"summary": "Some text."})
        assert result["breakdown"]["experience"] == 0

    def test_long_experience_scores_fifteen(self):
        long_exp = "Led a team. " * 40  # ~400+ chars
        result = ats(sections={"experience": long_exp})
        assert result["breakdown"]["experience"] == 15

    def test_short_experience_scores_five(self):
        result = ats(sections={"experience": "Worked somewhere briefly."})
        assert result["breakdown"]["experience"] == 5


# ---------------------------------------------------------------------------
# Tests: Skills (20 pts)
# ---------------------------------------------------------------------------

class TestSkillsScore:

    def test_zero_skills_scores_zero(self):
        result = ats(skills=[])
        assert result["breakdown"]["skills"] == 0

    def test_fifteen_skills_scores_fifteen(self):
        result = ats(skills=[f"Skill{i}" for i in range(15)])
        assert result["breakdown"]["skills"] == 15

    def test_many_skills_capped_at_fifteen(self):
        result = ats(skills=[f"Skill{i}" for i in range(50)])
        assert result["breakdown"]["skills"] == 15

    def test_eight_skills_scores_proportionally(self):
        result = ats(skills=[f"Skill{i}" for i in range(8)])
        assert 0 < result["breakdown"]["skills"] < 15


# ---------------------------------------------------------------------------
# Tests: Resume length (5 pts)
# ---------------------------------------------------------------------------

class TestResumeLength:

    def test_optimal_length_scores_five(self):
        text = " ".join(["word"] * 500)
        result = ats(text=text)
        assert result["breakdown"]["resume_length"] == 5

    def test_very_short_scores_one(self):
        text = "Short resume."
        result = ats(text=text)
        assert result["breakdown"]["resume_length"] == 1

    def test_empty_text_scores_zero(self):
        result = ats(text="")
        assert result["breakdown"]["resume_length"] == 0


# ---------------------------------------------------------------------------
# Tests: All optional sections
# ---------------------------------------------------------------------------

class TestOptionalSections:

    def test_projects_present(self):
        result = ats(sections={"projects": "My project."})
        assert result["breakdown"]["projects"] == 10

    def test_projects_absent(self):
        result = ats(sections={"summary": "Summary."})
        assert result["breakdown"]["projects"] == 0

    def test_certifications_present(self):
        result = ats(sections={"certifications": "AWS cert."})
        assert result["breakdown"]["certifications"] == 10

    def test_education_present(self):
        result = ats(sections={"education": "B.Tech CS."})
        assert result["breakdown"]["education"] == 10
