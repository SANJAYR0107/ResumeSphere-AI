from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Any
import random
import uuid
from datetime import datetime

from backend.app.db.models import User, Course, Module, Lesson, Enrollment, Quiz, Question, Answer, Certificate, Badge, StudyGroup, GroupMember, Assignment, Submission, Leaderboard, Progress, Flashcard, LearningSession
from backend.app.db.database import engine
from backend.app.api.deps import get_db, get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/learning", tags=["AI Learning Platform"])

# --- Request Models ---
class GeneratePathReq(BaseModel):
    target_role: str
    current_skills: str

class ExecuteCodeReq(BaseModel):
    language: str
    code: str
    lesson_id: str

class QuizEvalReq(BaseModel):
    quiz_id: str
    answers: dict

class AskCopilotReq(BaseModel):
    question: str
    context: str

# --- MODULE H1: AI Course Generator ---
@router.post("/generate-path")
def generate_learning_path(req: GeneratePathReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mocking AI path generation
    course = Course(
        title=f"Mastering {req.target_role}",
        description=f"AI generated personalized path from your current skills: {req.current_skills}",
        difficulty="Intermediate",
        category="Tech",
        estimated_hours=40
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    # Auto enroll
    enroll = Enrollment(user_id=current_user.id, course_id=course.id)
    db.add(enroll)
    db.commit()
    
    return {"message": "Learning path generated successfully", "course_id": course.id}

# --- MODULE H2: Course Management ---
@router.get("/courses")
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).limit(10).all()
    if not courses:
        c1 = Course(title="Advanced Python for AI", description="Deep dive into Python for Machine Learning", difficulty="Advanced", category="AI", estimated_hours=20)
        c2 = Course(title="System Design Fundamentals", description="Learn how to scale distributed systems", difficulty="Intermediate", category="Architecture", estimated_hours=15)
        db.add_all([c1, c2])
        db.commit()
        courses = [c1, c2]
    return courses

# --- MODULE H3: Interactive Coding Lab ---
@router.post("/execute-code")
def execute_code(req: ExecuteCodeReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # SIMULATING BACKEND CODE EXECUTION
    # In a real environment, this must be sent to an isolated Docker container / WebAssembly
    
    is_success = "print" in req.code or "console.log" in req.code
    output = "Hello, World!" if is_success else "SyntaxError: Unexpected token"
    status = "success" if is_success else "error"
    
    sub = Submission(user_id=current_user.id, assignment_id="mock_assignment", code_content=req.code, score=100.0 if is_success else 0.0)
    db.add(sub)
    db.commit()
    
    return {
        "status": status,
        "output": output,
        "execution_time_ms": random.randint(12, 45),
        "ai_review": "Great use of standard I/O." if is_success else "Check your syntax on line 1."
    }

# --- MODULE H4: AI Quiz Engine ---
@router.post("/quiz/evaluate")
def evaluate_quiz(req: QuizEvalReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mocking evaluation
    score = random.randint(60, 100)
    return {
        "score": score,
        "passed": score >= 70,
        "feedback": "Excellent grasp of core concepts. Review memory management for a perfect score."
    }

# --- MODULE H5: Certification Engine ---
@router.get("/certificate/{course_id}")
def get_certificate(course_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cert = db.query(Certificate).filter(Certificate.user_id == current_user.id, Certificate.course_id == course_id).first()
    if not cert:
        cert = Certificate(user_id=current_user.id, course_id=course_id)
        db.add(cert)
        
        # Award badge
        badge = Badge(user_id=current_user.id, badge_name="Course Scholar", icon_url="/static/badges/scholar.png")
        db.add(badge)
        
        db.commit()
        db.refresh(cert)
    
    return {
        "verification_id": cert.verification_id,
        "issue_date": cert.issue_date,
        "student": current_user.full_name,
        "status": "Verified"
    }

# --- MODULE H6: Learning Analytics ---
@router.get("/analytics")
def get_learning_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "total_study_hours": random.randint(10, 120),
        "completion_rate": 65.5,
        "weak_areas": ["Dynamic Programming", "Concurrency"],
        "strong_areas": ["System Design", "Python Basics"]
    }

# --- MODULE H7: Collaborative Learning ---
@router.get("/groups")
def get_study_groups(db: Session = Depends(get_db)):
    groups = db.query(StudyGroup).all()
    if not groups:
        g = StudyGroup(name="Machine Learning Study Group", description="Prep for ML interviews")
        db.add(g)
        db.commit()
        groups = [g]
    return groups

# --- MODULE H8: AI Learning Assistant ---
@router.post("/ask-copilot")
def ask_learning_copilot(req: AskCopilotReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mocking LLM response
    return {
        "answer": f"Based on '{req.context}', the solution to your question '{req.question}' involves understanding the underlying abstraction. I recommend reviewing Module 3.",
        "related_topics": ["Abstraction", "Inheritance", "Polymorphism"]
    }

# --- MODULE H9: Gamification ---
@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lb = db.query(Leaderboard).filter(Leaderboard.user_id == current_user.id).first()
    if not lb:
        lb = Leaderboard(user_id=current_user.id, total_xp=random.randint(100, 5000), current_level=random.randint(1, 10), streak_days=random.randint(1, 15))
        db.add(lb)
        db.commit()
        
    return {
        "my_stats": {
            "xp": lb.total_xp,
            "level": lb.current_level,
            "streak": lb.streak_days
        },
        "top_users": [
            {"name": "Alice", "xp": 12500, "level": 25},
            {"name": "Bob", "xp": 9400, "level": 19},
            {"name": current_user.full_name, "xp": lb.total_xp, "level": lb.current_level}
        ]
    }
