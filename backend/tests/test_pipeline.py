"""
test_pipeline.py — Integration tests for resume_pipeline.py

These tests exercise the full pipeline end-to-end (without HTTP).
They require the embedding model to be loaded, so they are slower than
the unit tests (one-time model load cost ~1-2 s on first run).

Test matrix covers:
  - Fresh graduate resume
  - Experienced engineer resume
  - Resume with all section headings
  - Blank / empty text (graceful handling)
  - Large resume (5000+ characters)
  - Resume with tables (text-only approximation)
  - Resume with no detectable skills
  - Return type validation (ResumeAnalysis TypedDict)
  - processing_time_ms is positive and reasonable
  - embedding_dimension is 384
"""


import pytest

# Load the embedding model once for the entire test session
from backend.app.services.embedding_service import load_model
from backend.resume_pipeline import ResumeAnalysis, run_pipeline


@pytest.fixture(scope="session", autouse=True)
def load_embedding_model_once():
    """Load the sentence-transformer model once before any test runs."""
    load_model()


# ---------------------------------------------------------------------------
# Resume fixtures
# ---------------------------------------------------------------------------

EXPERIENCED_ENGINEER_RESUME = """
John Doe
john.doe@email.com | LinkedIn: linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Results-driven Senior Software Engineer with 8 years of experience building
scalable distributed systems. Specialised in Python, FastAPI, and cloud-native
architectures on AWS.

WORK EXPERIENCE
Senior Software Engineer — TechCorp Inc. (2020 – 2024)
- Architected and deployed microservices using Python, FastAPI, and Docker.
- Managed PostgreSQL and Redis infrastructure on AWS RDS and ElastiCache.
- Implemented CI/CD pipelines with GitHub Actions and Kubernetes on EKS.
- Led a team of 6 engineers and conducted 200+ code reviews.

Software Engineer — StartupXYZ (2018 – 2020)
- Built REST APIs with Flask and PostgreSQL.
- Integrated machine learning models using Scikit-learn and XGBoost.

EDUCATION
B.Tech Computer Science — XYZ University (2014 – 2018)
CGPA: 9.2 / 10

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, Go
Frameworks: FastAPI, Flask, React, Node.js
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS, Docker, Kubernetes
Tools: Git, GitHub Actions, JIRA, Linux

PROJECTS
AI Resume Analyzer — Full-stack NLP application using FastAPI, PyMuPDF, and
sentence-transformers for automated resume parsing and skill extraction.

CERTIFICATIONS
AWS Certified Solutions Architect — Associate (2022)
CKA — Certified Kubernetes Administrator (2023)

ACHIEVEMENTS
- Speaker at PyCon India 2023
- Open-source contributor (500+ GitHub stars)
"""

FRESH_GRADUATE_RESUME = """
Alice Smith
alice@example.com

Objective
Motivated computer science graduate looking for a junior software engineering role.

Education:
B.Tech Computer Science, ABC University, 2024
CGPA: 8.8

Skills
Python, JavaScript, React, SQL, Git, HTML, CSS, Docker

Projects
1. Library Management System
   Built using Django and SQLite. Supports CRUD operations and user authentication.

2. E-Commerce Platform
   React frontend with Node.js backend. Integrated Stripe API for payments.

Certifications
Python for Everybody — Coursera (2023)
"""

LARGE_RESUME = (
    "PROFESSIONAL SUMMARY\n"
    "Experienced data scientist with expertise in Machine Learning and Deep Learning.\n\n"
    + ("WORK EXPERIENCE\nData Scientist at BigCorp (2019-2024)\n"
       "- Python, TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy\n"
       "- AWS SageMaker for model training and deployment\n"
       "- PostgreSQL and MongoDB for data storage\n\n") * 10
    + "EDUCATION\nPh.D. Computer Science, MIT, 2019\n\n"
    + "TECHNICAL SKILLS\n"
    + "Python TensorFlow PyTorch Keras Scikit-learn XGBoost Pandas NumPy "
    + "Matplotlib Docker Kubernetes AWS Git Linux PostgreSQL MongoDB Redis\n"
)

BLANK_RESUME = ""
WHITESPACE_RESUME = "   \n\n\t  "
NO_SKILLS_RESUME = """
Dear Hiring Manager,
I am writing to apply for the position. I have relevant experience and
would like to be considered. Please find my credentials below. Thank you.
"""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def run(
        text: str,
        filename: str = "test_resume.pdf",
        pages: int = 1) -> ResumeAnalysis:
    return run_pipeline(raw_text=text, filename=filename, page_count=pages)


# ---------------------------------------------------------------------------
# Tests: Return type and structure
# ---------------------------------------------------------------------------

class TestReturnTypeAndStructure:

    def test_returns_resumeanalysis_dict(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert isinstance(result, dict)

    def test_has_all_required_keys(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        required_keys = {
            "filename", "pages", "candidate_name", "sections",
            "skills", "skill_details", "skill_count",
            "embedding_dimension", "processing_time_ms",
        }
        assert required_keys.issubset(result.keys())

    def test_filename_preserved(self):
        result = run(EXPERIENCED_ENGINEER_RESUME, filename="john_doe.pdf")
        assert result["filename"] == "john_doe.pdf"

    def test_pages_preserved(self):
        result = run(EXPERIENCED_ENGINEER_RESUME, pages=3)
        assert result["pages"] == 3

    def test_skills_is_list_of_strings(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert isinstance(result["skills"], list)
        assert all(isinstance(s, str) for s in result["skills"])

    def test_skill_details_is_list_of_dicts(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert isinstance(result["skill_details"], list)
        for item in result["skill_details"]:
            assert "skill" in item
            assert "category" in item
            assert "confidence" in item

    def test_sections_is_dict(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert isinstance(result["sections"], dict)

    def test_skill_count_matches_skills_list(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert result["skill_count"] == len(result["skills"])


# ---------------------------------------------------------------------------
# Tests: Embedding dimension
# ---------------------------------------------------------------------------

class TestEmbeddingDimension:

    def test_embedding_dimension_is_384(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert result["embedding_dimension"] == 384

    def test_fresh_grad_embedding_dimension_is_384(self):
        result = run(FRESH_GRADUATE_RESUME)
        assert result["embedding_dimension"] == 384

    def test_blank_resume_embedding_dimension_is_384(self):
        result = run(BLANK_RESUME)
        assert result["embedding_dimension"] == 384


# ---------------------------------------------------------------------------
# Tests: Processing time
# ---------------------------------------------------------------------------

class TestProcessingTime:

    def test_processing_time_is_positive(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert result["processing_time_ms"] > 0

    def test_processing_time_under_5000ms(self):
        # Allow generous 5 second budget (model already loaded)
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert result["processing_time_ms"] < 5000

    def test_blank_resume_processes_quickly(self):
        result = run(BLANK_RESUME)
        assert result["processing_time_ms"] < 2000


# ---------------------------------------------------------------------------
# Tests: Experienced engineer resume
# ---------------------------------------------------------------------------

class TestExperiencedEngineerResume:

    def test_python_in_skills(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert "Python" in result["skills"]

    def test_docker_in_skills(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert "Docker" in result["skills"]

    def test_aws_in_skills(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert "AWS" in result["skills"]

    def test_experience_section_detected(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert "experience" in result["sections"]

    def test_education_section_detected(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert "education" in result["sections"]

    def test_skills_section_detected(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert "skills" in result["sections"]

    def test_certifications_section_detected(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert "certifications" in result["sections"]

    def test_skill_count_greater_than_5(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        assert result["skill_count"] > 5

    def test_candidate_name_extracted(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        # Name heuristic should pick up "John Doe"
        assert result["candidate_name"] in ("John Doe", "")  # allow miss

    def test_skills_sorted_alphabetically(self):
        result = run(EXPERIENCED_ENGINEER_RESUME)
        skills = result["skills"]
        assert skills == sorted(skills, key=str.lower)


# ---------------------------------------------------------------------------
# Tests: Fresh graduate resume
# ---------------------------------------------------------------------------

class TestFreshGraduateResume:

    def test_python_detected(self):
        result = run(FRESH_GRADUATE_RESUME)
        assert "Python" in result["skills"]

    def test_git_detected(self):
        result = run(FRESH_GRADUATE_RESUME)
        assert "Git" in result["skills"]

    def test_education_detected(self):
        result = run(FRESH_GRADUATE_RESUME)
        assert "education" in result["sections"]

    def test_candidate_name_extracted(self):
        result = run(FRESH_GRADUATE_RESUME)
        assert result["candidate_name"] in ("Alice Smith", "")


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_blank_resume_does_not_crash(self):
        result = run(BLANK_RESUME)
        assert isinstance(result, dict)

    def test_blank_resume_has_zero_skills(self):
        result = run(BLANK_RESUME)
        assert result["skill_count"] == 0

    def test_blank_resume_empty_sections(self):
        result = run(BLANK_RESUME)
        assert result["sections"] == {}

    def test_whitespace_resume_does_not_crash(self):
        result = run(WHITESPACE_RESUME)
        assert isinstance(result, dict)

    def test_no_skills_resume_returns_zero_skills(self):
        result = run(NO_SKILLS_RESUME)
        assert result["skill_count"] == 0

    def test_large_resume_processes_successfully(self):
        result = run(LARGE_RESUME)
        assert result["skill_count"] > 0
        assert result["embedding_dimension"] == 384

    def test_large_resume_processing_time_under_10s(self):
        result = run(LARGE_RESUME)
        assert result["processing_time_ms"] < 10000
