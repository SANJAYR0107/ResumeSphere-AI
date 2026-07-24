"""
test_phase5_interview_platform.py - Test Suite for Phase B AI Interview Platform

Verifies:
1. interview_generator_service (question generation across categories and skills)
2. interview_evaluator_service (answer evaluation, scoring /10, follow-up questions)
3. interview_session_service (session lifecycle, next/prev/skip, timer, state persistence)
4. coding_interview_service (syntax validation, test case execution, complexity analysis)
5. interview_report_service (ReportLab PDF generation)
6. API Endpoints:
   - POST /api/interview/session/start
   - POST /api/interview/session/submit-answer
   - POST /api/interview/coding/execute
   - GET /api/interview/history
   - GET /api/interview/analytics
   - POST /api/interview/download-report
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.services.interview_generator_service import generate_interview_questions
from backend.app.services.interview_evaluator_service import evaluate_answer
from backend.app.services.interview_session_service import (
    create_interview_session,
    submit_session_answer,
    compute_dashboard_analytics,
)
from backend.app.services.coding_interview_service import execute_and_review_code
from backend.app.services.interview_report_service import generate_interview_pdf_report

client = TestClient(app)


def test_interview_generator_service():
    questions = generate_interview_questions(
        resume_skills=["Java", "Spring Boot"],
        missing_skills=["Docker", "AWS"],
        interview_type="Experienced",
        difficulty="Medium",
        question_count=5,
        target_role="Java Backend Engineer",
        target_company="Acme Corp"
    )
    assert len(questions) == 5
    assert any(q["category"] == "Technical" for q in questions)
    assert any(q["category"] == "Behavioral" for q in questions)
    assert questions[0]["question_id"] == "q_1"


def test_interview_evaluator_service():
    eval_res = evaluate_answer(
        question_text="Explain Java Garbage Collection algorithms.",
        answer_text="Java uses generational garbage collection with Eden space and Survivor spaces managed by G1GC.",
        expected_concepts=["Garbage Collection", "Generational Heap", "Eden Space", "G1GC / ZGC"],
        target_skill="Java"
    )
    assert eval_res["overall_score"] > 6.0
    assert "Eden Space" in eval_res["matched_keywords"]
    assert eval_res["follow_up_question"] is not None


def test_interview_session_lifecycle():
    session = create_interview_session(
        resume_skills=["Python", "FastAPI"],
        missing_skills=["Kubernetes"],
        question_count=3
    )
    session_id = session["session_id"]
    assert session["status"] == "IN_PROGRESS"
    assert session["total_questions"] == 3

    # Submit Answer 1
    sub1 = submit_session_answer(
        session_id=session_id,
        question_id="q_1",
        candidate_answer="Python uses Global Interpreter Lock GIL for memory safety.",
        time_spent_seconds=30
    )
    assert sub1["status"] == "IN_PROGRESS"
    assert sub1["evaluation"]["overall_score"] > 0

    # Skip Answer 2
    sub2 = submit_session_answer(
        session_id=session_id,
        question_id="q_2",
        candidate_answer="",
        skip=True
    )
    assert sub2["evaluation"]["overall_score"] == 0.0

    # Analytics check
    analytics = compute_dashboard_analytics()
    assert analytics["total_interviews"] >= 1


def test_coding_interview_service():
    code_input = """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []
"""
    review = execute_and_review_code(code_input, language="python")
    assert review["status"] == "ACCEPTED"
    assert review["passed_test_cases"] == 3
    assert review["time_complexity"] == "O(N)"


def test_interview_report_pdf_generation():
    session_data = {
        "target_role": "Senior Software Engineer",
        "target_company": "Acme Inc",
        "submissions": {
            "q_1": {
                "evaluation": {
                    "overall_score": 8.5,
                    "technical_accuracy_score": 9.0,
                    "communication_score": 8.0,
                    "confidence_score": 8.5,
                    "strengths": ["Clear technical explanation"],
                    "weaknesses": ["Minor depth additions"]
                }
            }
        }
    }
    pdf_bytes = generate_interview_pdf_report(session_data)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_api_start_interview_session():
    payload = {
        "resume_skills": ["Python", "Docker"],
        "missing_skills": ["Kubernetes"],
        "question_count": 3
    }
    res = client.post("/api/interview/session/start", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert len(data["questions"]) == 3


def test_api_coding_execute():
    payload = {
        "code_text": "def solution(): return True",
        "language": "python"
    }
    res = client.post("/api/interview/coding/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ACCEPTED"


def test_api_analytics_and_history():
    res_hist = client.get("/api/interview/history")
    assert res_hist.status_code == 200

    res_analytics = client.get("/api/interview/analytics")
    assert res_analytics.status_code == 200
    data = res_analytics.json()
    assert "total_interviews" in data


def test_api_interview_download_report():
    payload = {
        "target_role": "AI Architect",
        "submissions": {}
    }
    res = client.post("/api/interview/download-report", json=payload)
    assert res.status_code == 200
    assert res.headers.get("content-type") == "application/pdf"
    assert res.content.startswith(b"%PDF")
