from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Any
import random
import uuid
import time
from datetime import datetime

from backend.app.db.models import User, Organization, TalentGraphNode, TalentGraphEdge, CandidateRanking, SalaryBenchmark, WorkforcePlan
from backend.app.db.database import engine
from backend.app.api.deps import get_db, get_current_user, requires_role
from pydantic import BaseModel

router = APIRouter(prefix="/api/talent", tags=["AI Talent Intelligence"])

# --- Models ---
class RankingReq(BaseModel):
    job_role: str

class PlanReq(BaseModel):
    department: str
    forecasted_hires: int
    target_quarter: str
    budget: int

# --- MODULE G1: Talent Knowledge Graph ---
@router.get("/graph")
def get_talent_graph(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR", "Recruiter"]))):
    # Mock returning nodes and edges for graph visualization
    nodes = [
        {"id": "n1", "label": "Python", "group": "skill"},
        {"id": "n2", "label": "Data Scientist", "group": "role"},
        {"id": "n3", "label": "Candidate A", "group": "candidate"},
        {"id": "n4", "label": "Candidate B", "group": "candidate"},
        {"id": "n5", "label": "TechCorp", "group": "company"}
    ]
    edges = [
        {"from": "n3", "to": "n1", "label": "HAS_SKILL"},
        {"from": "n4", "to": "n1", "label": "HAS_SKILL"},
        {"from": "n3", "to": "n5", "label": "WORKED_AT"},
        {"from": "n2", "to": "n1", "label": "REQUIRES"}
    ]
    return {"nodes": nodes, "edges": edges}

# --- MODULE G2: AI Candidate Ranking Engine ---
@router.post("/ranking")
def generate_rankings(req: RankingReq, db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR", "Recruiter"]))):
    # Generate mock rankings
    candidates = db.query(User).filter(User.role == "Candidate").limit(5).all()
    rankings = []
    for c in candidates:
        match_score = random.uniform(60.0, 99.9)
        rank = CandidateRanking(
            candidate_id=c.id,
            job_role=req.job_role,
            match_score=match_score,
            confidence_score=match_score - random.uniform(2.0, 10.0)
        )
        db.add(rank)
        rankings.append({
            "name": c.full_name,
            "match_score": round(rank.match_score, 1),
            "confidence": round(rank.confidence_score, 1)
        })
    db.commit()
    return sorted(rankings, key=lambda x: x['match_score'], reverse=True)

# --- MODULE G3: Predictive Hiring ---
@router.get("/predict")
def predict_hiring_success(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR"]))):
    # Mock predictive metrics
    return {
        "time_to_fill_days": random.randint(14, 45),
        "offer_acceptance_probability": 85.5,
        "flight_risk_candidates": 3,
        "recommended_action": "Increase outreach for Senior Engineers; market demand is spiking."
    }

# --- MODULE G4: Salary Benchmarking ---
@router.get("/salary")
def get_salary_benchmarks(role: str = "Software Engineer", location: str = "Remote", db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR", "Recruiter"]))):
    # Check DB or mock
    bench = db.query(SalaryBenchmark).filter(SalaryBenchmark.role == role, SalaryBenchmark.location == location).first()
    if not bench:
        bench = SalaryBenchmark(
            role=role,
            location=location,
            average_salary=random.randint(120000, 160000),
            min_salary=90000,
            max_salary=200000
        )
        db.add(bench)
        db.commit()
    return bench

# --- MODULE G5: Skill Intelligence ---
@router.get("/skills")
def get_skill_intelligence(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR", "Recruiter"]))):
    return {
        "trending_up": ["Rust", "Go", "Prompt Engineering", "LLMOps"],
        "trending_down": ["jQuery", "AngularJS"],
        "critical_gaps_in_org": ["Cloud Architecture", "System Design"]
    }

# --- MODULE G6: Talent Heatmaps ---
@router.get("/heatmap")
def get_talent_heatmap(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR", "Recruiter"]))):
    # Mock geospatial or functional heatmap data
    return [
        {"region": "North America", "talent_density": 85},
        {"region": "Europe", "talent_density": 65},
        {"region": "Asia", "talent_density": 70},
        {"region": "Remote", "talent_density": 95}
    ]

# --- MODULE G7: Workforce Planning ---
@router.post("/workforce")
def create_workforce_plan(req: PlanReq, db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR"]))):
    # Using a mock org
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="ResumeSphere Enterprise", industry="Technology")
        db.add(org)
        db.commit()

    plan = WorkforcePlan(
        organization_id=org.id,
        department=req.department,
        forecasted_hires=req.forecasted_hires,
        target_quarter=req.target_quarter,
        budget=req.budget
    )
    db.add(plan)
    db.commit()
    return {"message": "Workforce plan generated", "plan_id": plan.id}

# --- MODULE G8: Executive Dashboards ---
@router.get("/dashboard")
def get_executive_dashboard(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR", "Recruiter"]))):
    return {
        "active_candidates": random.randint(500, 2000),
        "open_requisitions": random.randint(10, 50),
        "ai_match_efficiency": 92.5,
        "diversity_index": 78.0,
        "cost_per_hire": "$4,250"
    }
