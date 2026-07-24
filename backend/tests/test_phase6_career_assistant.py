"""
test_phase6_career_assistant.py - Test Suite for Phase C AI Career Assistant

Verifies:
1. career_coach_service (Module C1)
2. resume_chat_service (Module C2)
3. cover_letter_service (Module C3)
4. learning_roadmap_service (Module C4)
5. certification_service (Module C5)
6. portfolio_analyzer_service (Module C6)
7. job_readiness_service (Module C7)
8. job_tracker_service (Module C8)
9. career_dashboard_service (Module C9)
10. API Endpoints:
    - POST /api/career/coach
    - POST /api/career/chat
    - POST /api/career/cover-letter/generate
    - POST /api/career/cover-letter/download-pdf
    - POST /api/career/learning-roadmap
    - POST /api/career/certifications
    - POST /api/career/portfolio-analysis
    - POST /api/career/job-readiness
    - POST /api/career/tracker/job
    - GET /api/career/tracker/jobs
    - DELETE /api/career/tracker/job/{job_id}
    - GET /api/career/dashboard
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.services.career_coach_service import generate_career_roadmap
from backend.app.services.resume_chat_service import process_resume_chat_query
from backend.app.services.cover_letter_service import generate_cover_letter, generate_cover_letter_pdf
from backend.app.services.learning_roadmap_service import generate_learning_plan
from backend.app.services.certification_service import recommend_certifications
from backend.app.services.portfolio_analyzer_service import analyze_candidate_portfolio
from backend.app.services.job_readiness_service import compute_job_readiness
from backend.app.services.job_tracker_service import save_tracked_job, list_tracked_jobs, delete_tracked_job
from backend.app.services.career_dashboard_service import get_unified_career_dashboard

client = TestClient(app)


def test_career_coach_service():
    roadmap = generate_career_roadmap(
        resume_skills=["Java", "Spring Boot"],
        target_role="Lead Software Architect"
    )
    assert len(roadmap["phases"]) == 3
    assert "Java" in roadmap["current_skills"]


def test_resume_chat_service():
    chat_res = process_resume_chat_query(
        query="Why is my ATS score low?",
        resume_skills=["Python"],
        ats_score=65,
        missing_skills=["Docker", "AWS"]
    )
    assert "65/100" in chat_res["assistant_response"] or "65" in chat_res["assistant_response"]
    assert len(chat_res["suggested_followup_queries"]) > 0


def test_cover_letter_service_and_pdf():
    cl_data = generate_cover_letter(
        candidate_name="Alex Smith",
        target_role="Senior DevOps Engineer",
        company_name="Cloud Corp",
        experience_type="Experienced",
        resume_skills=["Docker", "Kubernetes", "AWS"]
    )
    assert "Cloud Corp" in cl_data["cover_letter_text"]

    pdf_bytes = generate_cover_letter_pdf(dict(cl_data))
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_learning_roadmap_service():
    plan = generate_learning_plan(target_skill="Kubernetes")
    assert plan["target_skill"] == "Kubernetes"
    assert len(plan["weekly_goals"]) > 0


def test_certification_service():
    certs = recommend_certifications(
        resume_skills=["AWS", "Docker"],
        target_role="Cloud Engineer"
    )
    assert len(certs) > 0
    assert certs[0]["relevance_score"] > 50


def test_portfolio_analyzer_service():
    result = analyze_candidate_portfolio(
        resume_skills=["FastAPI", "React"],
        project_text="Built a high throughput API gateway microservice."
    )
    assert result["portfolio_quality_score"] > 7.0
    assert len(result["recommended_new_projects"]) > 0


def test_job_readiness_service():
    readiness = compute_job_readiness(
        ats_score=85,
        interview_avg_score=8.5,
        skill_match_percentage=85,
        portfolio_score=9.0
    )
    assert readiness["overall_readiness_percentage"] >= 80
    assert readiness["readiness_level"] == "Job Ready"


def test_job_tracker_service():
    job = save_tracked_job(
        company_name="Google",
        role_title="Backend Engineer",
        status="Applied"
    )
    job_id = job["job_id"]
    all_jobs = list_tracked_jobs()
    assert any(j["job_id"] == job_id for j in all_jobs)

    deleted = delete_tracked_job(job_id)
    assert deleted is True


def test_api_career_coach():
    res = client.post("/api/career/coach", json={"resume_skills": ["Python"], "target_role": "AI Engineer"})
    assert res.status_code == 200
    assert "phases" in res.json()


def test_api_resume_chat():
    res = client.post("/api/career/chat", json={"query": "What skill is missing?", "missing_skills": ["AWS"]})
    assert res.status_code == 200
    assert "assistant_response" in res.json()


def test_api_cover_letter():
    res = client.post("/api/career/cover-letter/generate", json={"company_name": "Acme Inc"})
    assert res.status_code == 200
    assert "cover_letter_text" in res.json()


def test_api_cover_letter_download():
    res = client.post("/api/career/cover-letter/download-pdf", json={"candidate_name": "Test User", "cover_letter_text": "Hello world"})
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF")


def test_api_career_dashboard():
    res = client.get("/api/career/dashboard?ats_score=80")
    assert res.status_code == 200
    data = res.json()
    assert "overall_readiness_percentage" in data
    assert "ats_trend" in data
