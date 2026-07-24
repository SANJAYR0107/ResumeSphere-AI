from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Any
import random
import json

from backend.app.db.models import User, Portfolio, GitHubProfile, LinkedInProfile, Mentor, Session as MentorSession, CommunityPost, JobAlert, LearningGoal, Notification
from backend.app.db.database import engine
from backend.app.api.deps import get_db, get_current_user, requires_role
from pydantic import BaseModel

router = APIRouter(prefix="/api/ecosystem", tags=["AI Career Ecosystem"])

# --- Models ---
class GitHubReq(BaseModel):
    username: str

class LinkedInReq(BaseModel):
    profile_url: str

class PostReq(BaseModel):
    title: str
    content: str
    category: str = "Discussion"

class PortfolioReq(BaseModel):
    theme: str
    projects: list
    skills: list

# --- MODULE E1: AI Portfolio Builder ---
@router.post("/portfolio")
def generate_portfolio(req: PortfolioReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    port = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not port:
        port = Portfolio(user_id=current_user.id)
        db.add(port)
    
    port.theme = req.theme
    port.projects = req.projects
    port.skills = req.skills
    db.commit()
    return {"message": "Portfolio updated successfully", "portfolio_id": port.id}

@router.get("/portfolio/export")
def export_portfolio(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    port = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # Return mock HTML/JSON representation
    return {"html": f"<html><body><h1>{current_user.full_name}'s Portfolio ({port.theme})</h1></body></html>"}

# --- MODULE E2: GitHub Analyzer ---
@router.post("/analyze/github")
def analyze_github(req: GitHubReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock AI analysis of GitHub
    score = random.uniform(70, 95)
    gh = GitHubProfile(
        user_id=current_user.id,
        username=req.username,
        commit_activity=random.randint(100, 1000),
        code_quality_score=score,
        top_languages=["Python", "JavaScript", "Go"],
        repository_score=score + 2.0,
        recommendations=["Add more documentation", "Contribute to open source issues"]
    )
    db.add(gh)
    db.commit()
    db.refresh(gh)
    return gh

# --- MODULE E3: LinkedIn Profile Optimizer ---
@router.post("/analyze/linkedin")
def analyze_linkedin(req: LinkedInReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock AI analysis of LinkedIn
    strength = random.uniform(60, 90)
    li = LinkedInProfile(
        user_id=current_user.id,
        profile_url=req.profile_url,
        strength_score=strength,
        visibility_score=strength + 5.0,
        suggestions=["Add numbers to your achievements", "Update your headline to include keywords"]
    )
    db.add(li)
    db.commit()
    db.refresh(li)
    return li

# --- MODULE E4: AI Job Discovery ---
@router.get("/jobs/recommended")
def get_recommended_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        {"title": "Senior AI Engineer", "company": "TechNova", "match_score": 92, "salary": "$140k - $180k", "remote": True},
        {"title": "Backend Developer", "company": "DataCorp", "match_score": 85, "salary": "$110k - $140k", "remote": False}
    ]

# --- MODULE E5: Mentor Connect ---
@router.get("/mentors")
def list_mentors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Seed mock mentors if empty
    mentors = db.query(Mentor).all()
    if not mentors:
        mock_mentor = Mentor(user_id=current_user.id, expertise="System Design, ML", rating=4.9, bio="Senior Staff Engineer")
        db.add(mock_mentor)
        db.commit()
        mentors = [mock_mentor]
    return mentors

@router.post("/mentors/{mentor_id}/book")
def book_mentor_session(mentor_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = MentorSession(mentor_id=mentor_id, mentee_id=current_user.id)
    db.add(session)
    db.commit()
    return {"message": "Session booked successfully"}

# --- MODULE E6: Community Platform ---
@router.post("/community/posts")
def create_post(req: PostReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = CommunityPost(user_id=current_user.id, title=req.title, content=req.content, category=req.category)
    db.add(post)
    db.commit()
    return {"message": "Post created"}

@router.get("/community/posts")
def list_posts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    posts = db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).all()
    # Add some mock posts if empty
    if not posts:
        return [
            {"title": "How to prep for Google System Design?", "author": "Alice", "likes": 42},
            {"title": "Review my React Portfolio", "author": "Bob", "likes": 12}
        ]
    return posts

# --- MODULE E7: Smart Notifications ---
@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    if not notifs:
        return [
            {"message": "New job match: Senior AI Engineer at TechNova", "type": "job_match"},
            {"message": "Your mock interview session is tomorrow.", "type": "mentor_alert"}
        ]
    return notifs

# --- MODULE E8: AI Insights Engine ---
@router.get("/insights")
def get_career_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "market_demand_score": 88,
        "promotion_readiness": 75,
        "career_risk": 12,
        "emerging_skills": ["Rust", "GraphQL", "Kubernetes"],
        "advice": "Your skill demand is high. Focus on System Design for the next level."
    }

# --- MODULE E9: Unified Career Dashboard ---
@router.get("/dashboard")
def get_ecosystem_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "user": current_user.full_name,
        "role": current_user.role,
        "portfolio_status": "Active",
        "github_score": 82,
        "linkedin_score": 78,
        "learning_progress": 65,
        "active_applications": 3
    }
