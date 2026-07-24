from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import logging

from ..db.database import get_db
from ..db.models import (
    User, CareerGoal, CareerPlan, Task, JobRecommendation,
    SalaryInsight, VoiceSession, AutomationRule, Reminder,
    CareerMetric, AgentConversation, AgentMemory, Planner, GoalProgress, CareerReport
)
from ..services.copilot_ai_service import copilot_ai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copilot", tags=["AI Career Copilot"])

# --- Schemas ---

class AgentQuery(BaseModel):
    user_id: str
    query: str
    context: Dict[str, Any] = {}

class GoalCreate(BaseModel):
    user_id: str
    title: str
    description: str
    target_date: datetime

class AutomationRuleCreate(BaseModel):
    user_id: str
    trigger_event: str
    action_type: str

# --- Copilot Multi-Agent Hub ---

@router.post("/chat")
def chat_with_copilot(req: AgentQuery, db: Session = Depends(get_db)):
    """Routes the query to the correct AI Agent (Salary, Resume, Planning, etc.)"""
    response = copilot_ai.dispatch_query(req.query, req.context)
    
    # Log conversation
    db_conv = AgentConversation(
        user_id=req.user_id,
        agent_type=response.get("agent", "Coordinator"),
        query=req.query,
        response=response.get("response", "")
    )
    db.add(db_conv)
    db.commit()
    
    return response

# --- Goals and Planning ---

@router.post("/goals", status_code=status.HTTP_201_CREATED)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    db_goal = CareerGoal(**goal.model_dump())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    # Auto-generate a plan via AI
    plan = copilot_ai.generate_career_plan(db_goal.title)
    db_plan = CareerPlan(goal_id=db_goal.id, plan_content=json.dumps(plan))
    db.add(db_plan)
    db.commit()
    
    return {"goal": db_goal, "plan": plan}

@router.get("/goals/{user_id}")
def get_goals(user_id: str, db: Session = Depends(get_db)):
    goals = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).all()
    return goals

# --- Salary Insights ---

@router.get("/salary-insights")
def get_salary_insights(job_title: str, location: str, db: Session = Depends(get_db)):
    # Simple pass-through to AI service for benchmarking
    return copilot_ai.analyze_salary(job_title, location, 0)

# --- Automations ---

@router.post("/automations", status_code=status.HTTP_201_CREATED)
def configure_automation(rule: AutomationRuleCreate, db: Session = Depends(get_db)):
    db_rule = AutomationRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.get("/automations/{user_id}")
def get_automations(user_id: str, db: Session = Depends(get_db)):
    return db.query(AutomationRule).filter(AutomationRule.user_id == user_id).all()

# --- Voice / STT Logging ---

@router.post("/voice/log")
def log_voice_session(user_id: str, transcript: str, intent: str, db: Session = Depends(get_db)):
    db_voice = VoiceSession(user_id=user_id, transcript=transcript, intent_detected=intent)
    db.add(db_voice)
    db.commit()
    return {"status": "Logged"}
