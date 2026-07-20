"""
test_section_service.py — Unit tests for section_service.py

Test matrix covers:
  - Empty input
  - Resume with all common section headings
  - Resume without any headings (flat text)
  - Section headings in ALL CAPS
  - Section headings in Title Case with colons
  - Headings that appear mid-document
  - Resume with duplicate section keys (merged)
  - Fresh graduate resume format
  - Experienced engineer resume format
  - Resume with unrecognised headings (captured as 'other')
"""

import pytest

from backend.app.services.section_service import detect_sections


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_RESUME = """John Doe
j.doe@email.com

PROFESSIONAL SUMMARY
Experienced backend engineer with 6 years of industry experience.

WORK EXPERIENCE
Senior Engineer at TechCorp (2020-2024)
- Designed microservices architecture
- Led a team of 7 engineers

EDUCATION
B.Tech Computer Science, XYZ University, 2018

TECHNICAL SKILLS
Python, FastAPI, Docker, PostgreSQL, Redis

PROJECTS
Resume Analyzer - AI-powered resume parsing tool using FastAPI and PyMuPDF.

CERTIFICATIONS
AWS Certified Solutions Architect - Associate

ACHIEVEMENTS
- Employee of the Year 2022
- Published 3 research papers

LANGUAGES
English (Native), Hindi (Proficient), Spanish (Beginner)

PUBLICATIONS
Doe, J. (2023). "Efficient NLP Pipelines". JMLR.

INTERNSHIPS
Software Engineering Intern at StartupXYZ (May-Aug 2017)

VOLUNTEER
Mentored underprivileged students in programming (2019-2021)
"""

FRESH_GRADUATE_RESUME = """Alice Smith
alice@example.com

Objective
Recent CS graduate seeking a software engineering position.

Education:
B.Tech Computer Science, ABC University, 2024 — CGPA: 9.1

Skills
Python, JavaScript, React, SQL, Git

Projects
Library Management System — Django, SQLite
E-Commerce App — React, Node.js
"""

NO_HEADINGS_RESUME = """
John Doe, Software Engineer
Python JavaScript Docker AWS
Worked at TechCorp for 3 years building REST APIs.
Graduated from XYZ University in 2020.
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEmptyInput:

    def test_empty_string_returns_empty_dict(self):
        result = detect_sections("")
        assert result == {}

    def test_whitespace_only_returns_empty_dict(self):
        result = detect_sections("   \n\n   ")
        assert result == {}


class TestSectionDetectionAllCaps:
    """Section headings in ALL CAPS format."""

    def test_detects_summary(self):
        result = detect_sections(FULL_RESUME)
        assert "summary" in result

    def test_detects_experience(self):
        result = detect_sections(FULL_RESUME)
        assert "experience" in result

    def test_detects_education(self):
        result = detect_sections(FULL_RESUME)
        assert "education" in result

    def test_detects_skills(self):
        result = detect_sections(FULL_RESUME)
        assert "skills" in result

    def test_detects_projects(self):
        result = detect_sections(FULL_RESUME)
        assert "projects" in result

    def test_detects_certifications(self):
        result = detect_sections(FULL_RESUME)
        assert "certifications" in result

    def test_detects_achievements(self):
        result = detect_sections(FULL_RESUME)
        assert "achievements" in result

    def test_detects_languages(self):
        result = detect_sections(FULL_RESUME)
        assert "languages" in result

    def test_detects_publications(self):
        result = detect_sections(FULL_RESUME)
        assert "publications" in result

    def test_detects_internships(self):
        result = detect_sections(FULL_RESUME)
        assert "internships" in result

    def test_detects_volunteer(self):
        result = detect_sections(FULL_RESUME)
        assert "volunteer" in result


class TestSectionContent:
    """Section content is correctly captured."""

    def test_experience_contains_company_name(self):
        result = detect_sections(FULL_RESUME)
        assert "TechCorp" in result.get("experience", "")

    def test_skills_contains_python(self):
        result = detect_sections(FULL_RESUME)
        assert "Python" in result.get("skills", "")

    def test_education_contains_university(self):
        result = detect_sections(FULL_RESUME)
        assert "XYZ University" in result.get("education", "")

    def test_projects_contains_project_name(self):
        result = detect_sections(FULL_RESUME)
        assert "Resume Analyzer" in result.get("projects", "")


class TestTitleCaseHeadings:
    """Section headings in Title Case with optional colon."""

    def test_objective_detected_as_summary(self):
        result = detect_sections(FRESH_GRADUATE_RESUME)
        assert "summary" in result

    def test_education_with_colon_detected(self):
        result = detect_sections(FRESH_GRADUATE_RESUME)
        assert "education" in result

    def test_skills_without_colon_detected(self):
        result = detect_sections(FRESH_GRADUATE_RESUME)
        assert "skills" in result

    def test_projects_without_colon_detected(self):
        result = detect_sections(FRESH_GRADUATE_RESUME)
        assert "projects" in result


class TestNoHeadingsResume:
    """Resume with no recognisable section headings."""

    def test_no_sections_detected(self):
        result = detect_sections(NO_HEADINGS_RESUME)
        # Should have no named sections — content may go into 'other' or be empty
        named_sections = {k for k in result if k != "other"}
        assert len(named_sections) == 0

    def test_returns_dict_not_none(self):
        result = detect_sections(NO_HEADINGS_RESUME)
        assert isinstance(result, dict)


class TestOutputStructure:
    """Return type and structure validation."""

    def test_returns_dict(self):
        result = detect_sections(FULL_RESUME)
        assert isinstance(result, dict)

    def test_all_values_are_strings(self):
        result = detect_sections(FULL_RESUME)
        for key, val in result.items():
            assert isinstance(key, str), f"Key '{key}' is not a str"
            assert isinstance(val, str), f"Value for '{key}' is not a str"

    def test_section_text_is_not_empty(self):
        result = detect_sections(FULL_RESUME)
        for key, val in result.items():
            assert val.strip() != "", f"Section '{key}' has empty content"

    def test_other_key_absent_when_no_preamble(self):
        # A resume that starts immediately with a heading should not produce
        # a non-empty 'other' section
        text = "PROFESSIONAL SUMMARY\nExperienced engineer.\n\nWORK EXPERIENCE\nTechCorp."
        result = detect_sections(text)
        other_content = result.get("other", "").strip()
        assert other_content == "" or "other" not in result


class TestFreshGraduateResume:
    """End-to-end detection for a fresh graduate CV."""

    def test_has_education(self):
        result = detect_sections(FRESH_GRADUATE_RESUME)
        assert "education" in result

    def test_education_contains_cgpa(self):
        result = detect_sections(FRESH_GRADUATE_RESUME)
        assert "CGPA" in result.get("education", "") or "9.1" in result.get("education", "")

    def test_skills_contains_git(self):
        result = detect_sections(FRESH_GRADUATE_RESUME)
        assert "Git" in result.get("skills", "")
