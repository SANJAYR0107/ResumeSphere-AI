"""
interview_session_service.py - Phase B Interview Session, State & History Management

Purpose
-------
Manages interactive interview state sessions, answer submissions, timer state,
historical storage, session recovery, and dashboard analytics aggregation.
"""

import uuid
import time
import logging
from typing import TypedDict, Any

from backend.app.services.interview_generator_service import (
    generate_interview_questions,
    InterviewQuestion,
)
from backend.app.services.interview_evaluator_service import (
    evaluate_answer,
    AnswerEvaluationResult,
)

logger = logging.getLogger(__name__)


class SubmittedAnswerRecord(TypedDict):
    question_id: str
    question_text: str
    target_skill: str
    candidate_answer: str
    time_spent_seconds: int
    skipped: bool
    evaluation: AnswerEvaluationResult | None


class InterviewSessionState(TypedDict):
    session_id: str
    target_role: str
    target_company: str
    interview_type: str
    difficulty: str
    created_at_timestamp: float
    status: str  # "IN_PROGRESS", "COMPLETED"
    current_question_index: int
    total_questions: int
    questions: list[InterviewQuestion]
    submissions: dict[str, SubmittedAnswerRecord]
    timer_total_seconds: int


# In-memory storage for active and completed interview sessions
_INTERVIEW_SESSIONS_DB: dict[str, InterviewSessionState] = {}


def create_interview_session(
    resume_skills: list[str],
    missing_skills: list[str],
    interview_type: str = "Experienced",
    difficulty: str = "Medium",
    question_count: int = 5,
    target_role: str = "Software Engineer",
    target_company: str = "Tech Corporation"
) -> InterviewSessionState:
    """Create a new interactive interview session and initialize state."""
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    questions = generate_interview_questions(
        resume_skills=resume_skills,
        missing_skills=missing_skills,
        interview_type=interview_type,
        difficulty=difficulty,
        question_count=question_count,
        target_role=target_role,
        target_company=target_company
    )

    session_state = InterviewSessionState(
        session_id=session_id,
        target_role=target_role,
        target_company=target_company,
        interview_type=interview_type,
        difficulty=difficulty,
        created_at_timestamp=time.time(),
        status="IN_PROGRESS",
        current_question_index=0,
        total_questions=len(questions),
        questions=questions,
        submissions={},
        timer_total_seconds=0
    )

    _INTERVIEW_SESSIONS_DB[session_id] = session_state
    logger.info("Created new interview session '%s' with %d questions", session_id, len(questions))
    return session_state


def get_interview_session(session_id: str) -> InterviewSessionState | None:
    """Retrieve an existing interview session state."""
    return _INTERVIEW_SESSIONS_DB.get(session_id)


def submit_session_answer(
    session_id: str,
    question_id: str,
    candidate_answer: str,
    time_spent_seconds: int = 45,
    skip: bool = False
) -> dict[str, Any]:
    """Submit or skip an answer for a specific question in a session and evaluate it."""
    session = _INTERVIEW_SESSIONS_DB.get(session_id)
    if not session:
        raise ValueError(f"Interview session '{session_id}' not found.")

    # Find question
    target_q = next((q for q in session["questions"] if q["question_id"] == question_id), None)
    if not target_q:
        raise ValueError(f"Question '{question_id}' not found in session '{session_id}'.")

    if skip:
        eval_result = evaluate_answer(
            question_text=target_q["question_text"],
            answer_text="",
            expected_concepts=target_q["expected_key_concepts"],
            target_skill=target_q["target_skill"],
            question_id=question_id
        )
        record = SubmittedAnswerRecord(
            question_id=question_id,
            question_text=target_q["question_text"],
            target_skill=target_q["target_skill"],
            candidate_answer="[SKIPPED]",
            time_spent_seconds=time_spent_seconds,
            skipped=True,
            evaluation=eval_result
        )
    else:
        eval_result = evaluate_answer(
            question_text=target_q["question_text"],
            answer_text=candidate_answer,
            expected_concepts=target_q["expected_key_concepts"],
            target_skill=target_q["target_skill"],
            question_id=question_id
        )
        record = SubmittedAnswerRecord(
            question_id=question_id,
            question_text=target_q["question_text"],
            target_skill=target_q["target_skill"],
            candidate_answer=candidate_answer,
            time_spent_seconds=time_spent_seconds,
            skipped=False,
            evaluation=eval_result
        )

    session["submissions"][question_id] = record
    session["timer_total_seconds"] += time_spent_seconds

    # Advance current question pointer
    current_idx = session["questions"].index(target_q)
    if current_idx + 1 < session["total_questions"]:
        session["current_question_index"] = current_idx + 1
    else:
        session["status"] = "COMPLETED"

    return {
        "session_id": session_id,
        "status": session["status"],
        "current_question_index": session["current_question_index"],
        "total_questions": session["total_questions"],
        "evaluation": eval_result,
        "next_question": session["questions"][session["current_question_index"]] if session["status"] == "IN_PROGRESS" else None
    }


def list_interview_history() -> list[dict[str, Any]]:
    """Retrieve all historical interview sessions."""
    history: list[dict[str, Any]] = []
    for sid, sess in _INTERVIEW_SESSIONS_DB.items():
        scores = [sub["evaluation"]["overall_score"] for sub in sess["submissions"].values() if sub["evaluation"]]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        
        history.append({
            "session_id": sid,
            "target_role": sess["target_role"],
            "target_company": sess["target_company"],
            "difficulty": sess["difficulty"],
            "status": sess["status"],
            "created_at_timestamp": sess["created_at_timestamp"],
            "total_questions": sess["total_questions"],
            "completed_questions": len(sess["submissions"]),
            "average_score": avg_score
        })
    
    # Sort newest first
    history.sort(key=lambda x: x["created_at_timestamp"], reverse=True)
    return history


def delete_interview_session(session_id: str) -> bool:
    """Delete a historical interview session."""
    if session_id in _INTERVIEW_SESSIONS_DB:
        del _INTERVIEW_SESSIONS_DB[session_id]
        return True
    return False


def compute_dashboard_analytics() -> dict[str, Any]:
    """Compute aggregated dashboard analytics across all interview sessions."""
    sessions = list(_INTERVIEW_SESSIONS_DB.values())
    total_interviews = len(sessions)
    completed = [s for s in sessions if s["status"] == "COMPLETED"]
    
    all_scores: list[float] = []
    skill_scores_map: dict[str, list[float]] = {}

    for s in sessions:
        for sub in s["submissions"].values():
            if sub["evaluation"]:
                score = sub["evaluation"]["overall_score"]
                all_scores.append(score)
                skill = sub["target_skill"]
                if skill not in skill_scores_map:
                    skill_scores_map[skill] = []
                skill_scores_map[skill].append(score)

    avg_overall = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    skill_performance: list[dict[str, Any]] = []
    for skill, s_list in skill_scores_map.items():
        avg_s: float = round(sum(s_list) / len(s_list), 1)
        skill_performance.append({
            "skill": skill,
            "average_score": avg_s,
            "count": len(s_list)
        })

    skill_performance.sort(key=lambda x: float(x["average_score"]), reverse=True)

    strong_areas = [str(sp["skill"]) for sp in skill_performance if float(sp["average_score"]) >= 7.0][:3]
    weak_areas = [str(sp["skill"]) for sp in skill_performance if float(sp["average_score"]) < 7.0][:3]

    success_rate = min(100, int((len([s for s in all_scores if s >= 7.0]) / len(all_scores) * 100))) if all_scores else 100

    return {
        "total_interviews": total_interviews,
        "completed_interviews": len(completed),
        "average_score": avg_overall,
        "success_rate_percentage": success_rate,
        "strong_areas": strong_areas if strong_areas else ["Core Technology Stack"],
        "weak_areas": weak_areas if weak_areas else ["Advanced System Architecture"],
        "skill_performance": skill_performance
    }
