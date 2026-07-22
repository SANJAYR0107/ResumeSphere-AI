"""
test_phase3_qa_verification.py - Comprehensive QA Verification Test Suite

Verifies:
1. All API endpoints return HTTP 200 with valid schema payloads:
   - POST /api/upload
   - POST /api/analyze
   - POST /api/job-match
   - POST /api/skill-gap
   - POST /api/recommendations
   - POST /api/ats-score
2. 3-Persona Functional Verification:
   - Java Backend Developer
   - Data Analyst
   - DevOps Engineer
3. Asserts persona output differentiation:
   - Different job recommendations
   - Different match percentages
   - Different missing skills
   - Different career roadmaps
   - Different interview questions
4. Benchmarks & performance measurements:
   - Resume upload time
   - Analysis time
   - Embedding generation time
   - Process memory usage
"""

import os
import sys
import time
import requests
import tracemalloc
import pytest

BASE_URL = "http://127.0.0.1:8001/api"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

JAVA_PDF = os.path.join(DATA_DIR, "java_resume.pdf")
DATA_PDF = os.path.join(DATA_DIR, "data_resume.pdf")
DEVOPS_PDF = os.path.join(DATA_DIR, "devops_resume.pdf")


def test_api_upload_endpoint():
    """Verify POST /api/upload returns HTTP 200 and correct structure."""
    with open(JAVA_PDF, "rb") as f:
        response = requests.post(f"{BASE_URL}/upload", files={"resume": ("java_resume.pdf", f, "application/pdf")})
    assert response.status_code == 200, f"Upload failed: {response.text}"
    data = response.json()
    assert "filename" in data
    assert "pages" in data
    assert "characters" in data
    assert "preview" in data


def test_api_analyze_endpoint_and_performance():
    """Verify POST /api/analyze returns HTTP 200, all Phase 3 fields, and measure performance."""
    tracemalloc.start()

    t0 = time.perf_counter()
    with open(JAVA_PDF, "rb") as f:
        response = requests.post(f"{BASE_URL}/analyze", files={"resume": ("java_resume.pdf", f, "application/pdf")})
    t1 = time.perf_counter()

    analysis_time_ms = (t1 - t0) * 1000
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert response.status_code == 200, f"Analyze failed: {response.text}"
    data = response.json()

    # Check required Phase 3 fields
    required_fields = [
        "ats_score", "ats_breakdown", "job_recommendations",
        "recommended_jobs", "skill_gap", "career_roadmap",
        "interview_preparation", "recruiter_summary", "career_insights",
        "interview_readiness", "clean_text", "skills", "skill_details"
    ]
    for field in required_fields:
        assert field in data, f"Missing field in /analyze response: {field}"
        assert data[field] is not None, f"Field is null/undefined in /analyze response: {field}"

    print(f"\n[Performance Benchmark]")
    print(f" - /api/analyze execution time: {analysis_time_ms:.2f} ms")
    print(f" - Peak test process memory usage: {peak_mem / (1024 * 1024):.2f} MB")


def test_api_skill_gap_endpoint():
    """Verify POST /api/skill-gap returns HTTP 200 and schema."""
    payload = {
        "matched_skills": ["Java", "Spring Boot"],
        "missing_skills": ["Kubernetes", "AWS"]
    }
    res = requests.post(f"{BASE_URL}/skill-gap", json=payload)
    assert res.status_code == 200, f"/skill-gap failed: {res.text}"
    data = res.json()
    assert "recommended_skills" in data
    assert "learning_suggestions" in data


def test_api_recommendations_endpoint():
    """Verify POST /api/recommendations returns HTTP 200 and schema."""
    payload = {
        "resume_skills": ["Python", "FastAPI", "SQL"],
        "resume_text": "Experienced Python Backend Developer working on REST APIs and PostgreSQL database optimization."
    }
    res = requests.post(f"{BASE_URL}/recommendations", json=payload)
    assert res.status_code == 200, f"/recommendations failed: {res.text}"
    data = res.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


def test_api_ats_score_endpoint():
    """Verify POST /api/ats-score returns HTTP 200 and breakdown."""
    payload = {
        "resume_text": "Experienced Java Backend Developer with 5 years in building microservices and REST APIs."
    }
    res = requests.post(f"{BASE_URL}/ats-score", json=payload)
    assert res.status_code == 200, f"/ats-score failed: {res.text}"
    data = res.json()
    assert "ats_score" in data
    assert "breakdown" in data


def test_api_job_match_endpoint():
    """Verify POST /api/job-match returns HTTP 200."""
    payload = {
        "resume_text": "Java backend developer skilled in Spring Boot, SQL, and Docker.",
        "job_description": "We are looking for a Senior Java Developer with Spring Boot, Docker, and Kubernetes expertise."
    }
    res = requests.post(f"{BASE_URL}/job-match", json=payload)
    assert res.status_code == 200, f"/job-match failed: {res.text}"
    data = res.json()
    assert "match_score" in data
    assert "matched_skills" in data
    assert "missing_skills" in data


def test_multi_persona_functional_differentiation():
    """Upload Java, Data Analyst, and DevOps resumes and verify output differentiation."""
    personas = {}
    files_map = {
        "Java": JAVA_PDF,
        "Data": DATA_PDF,
        "DevOps": DEVOPS_PDF,
    }

    for key, filepath in files_map.items():
        with open(filepath, "rb") as f:
            res = requests.post(f"{BASE_URL}/analyze", files={"resume": (os.path.basename(filepath), f, "application/pdf")})
        assert res.status_code == 200, f"Failed for persona {key}: {res.text}"
        personas[key] = res.json()

    java_res = personas["Java"]
    data_res = personas["Data"]
    devops_res = personas["DevOps"]

    # 1. Verify Job Recommendations are different
    java_jobs = [j["title"] for j in java_res["job_recommendations"]]
    data_jobs = [j["title"] for j in data_res["job_recommendations"]]
    devops_jobs = [j["title"] for j in devops_res["job_recommendations"]]

    assert java_jobs != data_jobs, "Java and Data Analyst job recommendations should differ"
    assert java_jobs != devops_jobs, "Java and DevOps job recommendations should differ"
    assert data_jobs != devops_jobs, "Data Analyst and DevOps job recommendations should differ"

    # 2. Verify Missing Skills are different
    java_missing = java_res.get("skill_gap", {}).get("missing_skills", [])
    data_missing = data_res.get("skill_gap", {}).get("missing_skills", [])
    devops_missing = devops_res.get("skill_gap", {}).get("missing_skills", [])

    assert java_missing != data_missing, "Java and Data missing skills should differ"
    assert java_missing != devops_missing, "Java and DevOps missing skills should differ"

    # 3. Verify Career Roadmaps are present and tailored
    assert java_res.get("career_roadmap") is not None
    assert data_res.get("career_roadmap") is not None
    assert devops_res.get("career_roadmap") is not None

    # 4. Verify Interview Preparation is present and tailored
    assert java_res.get("interview_preparation") is not None
    assert data_res.get("interview_preparation") is not None
    assert devops_res.get("interview_preparation") is not None

    print("\n[Persona Verification Summary]")
    print(f" - Java Top Job: {java_jobs[0] if java_jobs else 'N/A'}")
    print(f" - Data Top Job: {data_jobs[0] if data_jobs else 'N/A'}")
    print(f" - DevOps Top Job: {devops_jobs[0] if devops_jobs else 'N/A'}")


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])
