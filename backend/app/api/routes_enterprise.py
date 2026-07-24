from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Any
import json
import random

from backend.app.db.models import User, Company, Job, CandidateProfile, Comment, ActivityLog, InterviewRecord
from backend.app.db.database import engine
from backend.app.api.deps import get_db, get_current_user, requires_role
from pydantic import BaseModel

router = APIRouter(prefix="/api/enterprise", tags=["Enterprise Recruitment"])

# --- Models for Request/Response ---
class JobCreate(BaseModel):
    title: str
    description: str
    requirements: str
    location: str

class CandidateSearch(BaseModel):
    skills: str = ""
    location: str = ""

class CommentCreate(BaseModel):
    text: str

# Helper to log activity
def log_activity(db: Session, user_id: str, action: str, details: str):
    log = ActivityLog(user_id=user_id, action=action, details=details)
    db.add(log)
    db.commit()

# --- MODULE D1: Recruiter Dashboard ---
@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "Recruiter", "HR"]))):
    active_jobs = db.query(Job).filter(Job.status == "Open").count()
    total_candidates = db.query(CandidateProfile).count()
    shortlisted = db.query(CandidateProfile).filter(CandidateProfile.is_shortlisted == True).count()
    
    return {
        "active_jobs": active_jobs,
        "total_candidates": total_candidates,
        "shortlisted_candidates": shortlisted,
        "recent_applications": [] # Would fetch recent from DB
    }

@router.post("/jobs")
def create_job(job: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "Recruiter"]))):
    # Ensure a default company exists for demo
    company = db.query(Company).first()
    if not company:
        company = Company(name="ResumeSphere Enterprise", industry="Tech")
        db.add(company)
        db.commit()
        db.refresh(company)

    new_job = Job(
        company_id=company.id,
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        location=job.location
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    log_activity(db, current_user.id, "Created Job", f"Job {new_job.title} created.")
    return {"message": "Job created successfully", "job_id": new_job.id}

@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    jobs = db.query(Job).all()
    return [{"id": j.id, "title": j.title, "status": j.status, "location": j.location} for j in jobs]


# --- MODULE D2: Candidate Management ---
@router.get("/candidates")
def search_candidates(skills: str = "", location: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(CandidateProfile)
    if skills:
        query = query.filter(CandidateProfile.skills.ilike(f"%{skills}%"))
    if location:
        query = query.filter(CandidateProfile.location.ilike(f"%{location}%"))
        
    candidates = query.all()
    return [{
        "id": c.id, "name": c.name, "skills": c.skills, 
        "overall_score": c.overall_score, "is_shortlisted": c.is_shortlisted,
        "is_bookmarked": c.is_bookmarked
    } for c in candidates]

@router.post("/candidates/{candidate_id}/bookmark")
def toggle_bookmark(candidate_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    candidate = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.is_bookmarked = not candidate.is_bookmarked
    db.commit()
    action = "Bookmarked" if candidate.is_bookmarked else "Unbookmarked"
    log_activity(db, current_user.id, action, f"{action} candidate {candidate.name}")
    return {"status": "success", "is_bookmarked": candidate.is_bookmarked}


# --- MODULE D3: AI Candidate Ranking ---
@router.post("/jobs/{job_id}/rank")
def rank_candidates_for_job(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "Recruiter", "HiringManager"]))):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    candidates = db.query(CandidateProfile).filter(CandidateProfile.job_id == job_id).all()
    
    # Mock AI Ranking Logic
    for c in candidates:
        # Simulate AI analysis based on skills match + ats score
        skill_match = random.uniform(60, 100)
        c.overall_score = (c.ats_score * 0.4) + (c.interview_score * 0.3) + (skill_match * 0.3)
        if c.overall_score > 85:
            c.hiring_recommendation = "Strong Hire"
        elif c.overall_score > 70:
            c.hiring_recommendation = "Hire"
        else:
            c.hiring_recommendation = "Reject"
            
    db.commit()
    log_activity(db, current_user.id, "Ranked Candidates", f"Ranked candidates for {job.title}")
    return {"message": "Candidates ranked successfully."}


# --- MODULE D4: Bulk Resume Processing ---
def process_bulk_resumes_task(job_id: str, file_names: list, db: Session):
    # This would parse PDFs, extract text, run ATS, and insert into CandidateProfile
    # For now, simulate inserting mock candidates
    for name in file_names:
        c = CandidateProfile(
            job_id=job_id,
            name=f"Parsed {name}",
            email=f"{name.split('.')[0]}@example.com",
            skills="Python, React, FastAPI",
            ats_score=random.uniform(60, 95)
        )
        db.add(c)
    db.commit()

@router.post("/bulk-upload/{job_id}")
async def bulk_upload_resumes(job_id: str, background_tasks: BackgroundTasks, files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "Recruiter"]))):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    file_names = [f.filename for f in files]
    background_tasks.add_task(process_bulk_resumes_task, job_id, file_names, db)
    log_activity(db, current_user.id, "Bulk Upload", f"Uploaded {len(files)} resumes for {job.title}")
    return {"message": f"Processing {len(files)} resumes in background."}


# --- MODULE D5: Team Collaboration ---
@router.post("/candidates/{candidate_id}/comments")
def add_comment(candidate_id: str, comment: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_comment = Comment(
        candidate_id=candidate_id,
        user_id=current_user.id,
        text=comment.text
    )
    db.add(new_comment)
    db.commit()
    log_activity(db, current_user.id, "Added Comment", f"Commented on candidate {candidate_id}")
    return {"status": "success"}

@router.get("/activity")
def get_activity_timeline(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(50).all()
    return [{"user": log.user_id, "action": log.action, "details": log.details, "time": log.created_at} for log in logs]


# --- MODULE D6: Company Interview Database ---
@router.get("/interview-db")
def get_interview_db(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(InterviewRecord).all()
    # If empty, return mock data
    if not records:
        return [
            {"company": "Google", "role": "Software Engineer", "difficulty": "Hard", "questions": ["Reverse linked list", "System design tinyurl"]},
            {"company": "Amazon", "role": "Backend Engineer", "difficulty": "Medium", "questions": ["Two sum", "Leadership principles"]}
        ]
    return [{"id": r.id, "role": r.role, "difficulty": r.difficulty, "questions": r.questions} for r in records]


# --- MODULE D7: Enterprise Analytics ---
@router.get("/analytics")
def get_enterprise_analytics(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR"]))):
    # Mock analytics for charts
    return {
        "hiring_funnel": {"sourced": 500, "applied": 300, "interviewed": 50, "offered": 10},
        "offer_ratio": 20.0,
        "skill_demand": {"Python": 120, "React": 95, "Docker": 60, "AWS": 80}
    }


# --- MODULE D8: Notification Center ---
@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock notifications for current user
    return [
        {"id": 1, "text": "Interview scheduled for John Doe.", "time": "10 mins ago", "read": False},
        {"id": 2, "text": "New resumes uploaded for Frontend Role.", "time": "1 hour ago", "read": True}
    ]
