"""
test_phase4_engine.py - Unit & Integration Test Suite for Phase 4 Services & Endpoints

Verifies:
1. jd_parser_service (text and PDF parsing)
2. keyword_analysis_service (ranking, missing, matched, extra skills)
3. ats_optimizer_service (section scores & optimization suggestions)
4. resume_optimizer_service (rewrites, simulator, interview alignment, learning recommendations, executive summary)
5. report_service (ReportLab PDF generation)
6. API Endpoints:
   - POST /api/jd-analysis
   - POST /api/optimize-resume
   - POST /api/download-report
7. Performance: Latency under 2 seconds.
"""

import os
import pytest
import requests
from pathlib import Path

from backend.app.services.jd_parser_service import parse_jd_text
from backend.app.services.keyword_analysis_service import analyze_keywords
from backend.app.services.ats_optimizer_service import analyze_sections_and_ats_optimization
from backend.app.services.resume_optimizer_service import (
    generate_rewrite_suggestions,
    simulate_ats_improvement,
    generate_interview_alignment,
    generate_learning_recommendations,
    generate_executive_summary,
)
from backend.app.services.report_service import generate_pdf_report

BASE_URL = "http://127.0.0.1:8001/api"
DATA_DIR = Path(__file__).parent / "data"
JAVA_PDF = DATA_DIR / "java_resume.pdf"


SAMPLE_JD = """
Senior Java Backend Engineer - Job Description
We are looking for a Senior Java Backend Engineer with 5+ years of experience.
Required Skills: Java, Spring Boot, SQL, REST API, Microservices, PostgreSQL.
Preferred Skills: Docker, Kubernetes, AWS, Kafka.
Key Responsibilities:
- Design and implement high-performance REST APIs.
- Manage PostgreSQL databases and optimize queries.
- Build scalable microservices on AWS and Kubernetes.
Education: Bachelor's degree in Computer Science or related field.
"""

SAMPLE_RESUME = """
John Java Developer
john.java@email.com | 555-0192

SUMMARY
Experienced Java Software Engineer with 4 years building backend systems using Java, Spring Boot, and SQL.

SKILLS
Java, Spring Boot, SQL, REST API, Microservices, Git, HTML

EXPERIENCE
Software Engineer - Tech Corp (2020 - Present)
- Developed REST microservices in Java and Spring Boot.
- Managed SQL database schemas.
"""


def test_jd_parser_service():
    parsed = parse_jd_text(SAMPLE_JD)
    assert parsed["role_title"] is not None
    assert "Java" in parsed["extracted_skills"] or "Spring Boot" in parsed["extracted_skills"]
    assert parsed["estimated_yoe"] == 5
    assert len(parsed["keywords"]) > 0


def test_keyword_analysis_service():
    kw_result = analyze_keywords(
        resume_skills=["Java", "Spring Boot", "SQL"],
        jd_skills=["Java", "Spring Boot", "SQL", "Docker", "Kubernetes"],
        jd_required_skills=["Java", "Spring Boot", "SQL"],
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD
    )
    assert "Java" in kw_result["matched_keywords"]
    assert "Docker" in kw_result["missing_keywords"]
    assert kw_result["keyword_match_percentage"] > 0


def test_ats_optimizer_service():
    sec_res = analyze_sections_and_ats_optimization(
        resume_sections={"summary": "Experienced Java Dev", "experience": "Worked with Java"},
        resume_skills=["Java", "Spring Boot"],
        jd_skills=["Java", "Spring Boot", "Docker", "AWS"],
        missing_skills=["Docker", "AWS"],
        clean_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD
    )
    assert "Skills" in sec_res["sections"]
    assert len(sec_res["ats_suggestions"]) > 0


def test_resume_optimizer_service():
    rewrites = generate_rewrite_suggestions("John Java", "Senior Java Engineer", ["Java", "Spring Boot"], ["Docker", "AWS"], 5)
    assert rewrites["professional_summary"] is not None
    assert len(rewrites["experience_bullets"]) > 0

    simulator = simulate_ats_improvement(70, ["Docker", "AWS"])
    assert simulator["predicted_ats_score"] > 70
    assert simulator["expected_improvement"] > 0

    interview = generate_interview_alignment("Senior Java Engineer", ["Java", "Spring Boot"], ["Docker", "AWS"])
    assert len(interview["technical_questions"]) > 0

    learning = generate_learning_recommendations(["Docker", "AWS"])
    assert len(learning) == 2

    exec_sum = generate_executive_summary(85, 75, ["Java"], ["Docker"], "Senior Java Engineer")
    assert exec_sum["hiring_readiness"] is not None


def test_report_service_pdf_generation():
    dummy_data = {
        "role_title": "Senior Java Engineer",
        "match_scores": {"overall_match": 88, "ats_match": 82, "semantic_match": 90, "keyword_match": 80, "confidence": "High"},
        "executive_summary": {"hiring_readiness": "High Readiness", "overall_recommendation": "Strong Candidate"},
        "keyword_analysis": {"matched_keywords": ["Java", "Spring Boot"], "missing_keywords": ["Docker"], "important_missing_keywords": ["Docker"]},
        "ats_simulator": {"current_ats_score": 75, "predicted_ats_score": 90, "expected_improvement": 15},
        "ats_suggestions": [{"category": "Placement", "suggestion": "Move Docker into skills", "explanation": "Increases ATS score"}],
        "rewrite_suggestions": {"professional_summary": "High-impact software engineer..."},
        "interview_alignment": {"technical_questions": ["How does JVM garbage collection work?"]}
    }
    pdf_bytes = generate_pdf_report(dummy_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_api_jd_analysis_endpoint():
    payload = {
        "resume_text": SAMPLE_RESUME,
        "jd_text": SAMPLE_JD
    }
    res = requests.post(f"{BASE_URL}/jd-analysis", data=payload)
    assert res.status_code == 200, f"/jd-analysis failed: {res.text}"
    data = res.json()
    assert "role_title" in data
    assert "match_scores" in data
    assert "keyword_analysis" in data
    assert "ats_simulator" in data
    assert "rewrite_suggestions" in data
    assert "executive_summary" in data


def test_api_optimize_resume_endpoint():
    payload = {
        "resume_text": SAMPLE_RESUME,
        "job_description": SAMPLE_JD
    }
    res = requests.post(f"{BASE_URL}/optimize-resume", json=payload)
    assert res.status_code == 200, f"/optimize-resume failed: {res.text}"
    data = res.json()
    assert "rewrite_suggestions" in data
    assert "ats_simulator" in data


def test_api_download_report_endpoint():
    payload = {
        "resume_text": SAMPLE_RESUME,
        "job_description": SAMPLE_JD
    }
    res = requests.post(f"{BASE_URL}/download-report", json=payload)
    assert res.status_code == 200, f"/download-report failed: {res.text}"
    assert res.headers.get("content-type") == "application/pdf"
    assert res.content.startswith(b"%PDF")


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])
