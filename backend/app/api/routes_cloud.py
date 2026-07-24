from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Any
import random
import uuid
import time
from datetime import datetime

from backend.app.db.models import User, OAuthAccount, CloudStorageFile, GitHubAccount, JobApplication, CalendarEvent, EmailLog, Webhook, ApiKey, AutomationTask, SystemMetric
from backend.app.db.database import engine
from backend.app.api.deps import get_db, get_current_user, requires_role
from pydantic import BaseModel

router = APIRouter(prefix="/api/cloud", tags=["Global AI Career Cloud"])

# --- Models ---
class OAuthReq(BaseModel):
    provider: str
    code: str

class GitHubSyncReq(BaseModel):
    username: str

class JobApplyReq(BaseModel):
    company_name: str
    job_title: str
    source: str

class ScheduleReq(BaseModel):
    title: str
    date: str # ISO string

class WebhookReq(BaseModel):
    url: str
    event_type: str

class AutomationReq(BaseModel):
    task_name: str


# --- MODULE F1: Multi Cloud Authentication ---
@router.post("/auth/oauth")
def oauth_login(req: OAuthReq, db: Session = Depends(get_db)):
    # Mocking OAuth Code Exchange
    if not req.code:
        raise HTTPException(status_code=400, detail="Invalid OAuth code")
        
    # Simulate finding or creating a user
    mock_email = f"user_{req.code}@example.com"
    user = db.query(User).filter(User.email == mock_email).first()
    if not user:
        user = User(email=mock_email, hashed_password="oauth_managed", full_name=f"{req.provider} User", role="Candidate")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    oauth = db.query(OAuthAccount).filter(OAuthAccount.user_id == user.id, OAuthAccount.provider == req.provider).first()
    if not oauth:
        oauth = OAuthAccount(user_id=user.id, provider=req.provider, provider_account_id=req.code, access_token="mock_access", refresh_token="mock_refresh")
        db.add(oauth)
        db.commit()

    # In reality, this would return a JWT session token. Returning mock for UI demo
    from backend.app.api.deps import create_access_token
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "full_name": user.full_name}


# --- MODULE F2: Cloud Storage ---
@router.post("/storage/upload")
async def upload_file_to_cloud(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock S3/Azure Upload
    file_record = CloudStorageFile(
        user_id=current_user.id,
        filename=file.filename,
        provider="AWS S3",
        url=f"https://s3.amazonaws.com/resumesphere-mock/{uuid.uuid4()}/{file.filename}"
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return {"message": "File uploaded to cloud", "file": {"id": file_record.id, "url": file_record.url}}

@router.get("/storage/files")
def list_cloud_files(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    files = db.query(CloudStorageFile).filter(CloudStorageFile.user_id == current_user.id).all()
    return files


# --- MODULE F3: Live GitHub Integration ---
@router.post("/github/sync")
def sync_github(req: GitHubSyncReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    gh = db.query(GitHubAccount).filter(GitHubAccount.user_id == current_user.id).first()
    if not gh:
        gh = GitHubAccount(user_id=current_user.id)
        db.add(gh)
    
    # Mock live sync
    gh.username = req.username
    gh.total_commits = random.randint(300, 2500)
    gh.top_languages = "Python, TypeScript, Rust"
    gh.developer_score = random.uniform(7.5, 9.9)
    gh.last_synced = datetime.utcnow()
    db.commit()
    
    return {"message": "GitHub synchronized", "stats": {"commits": gh.total_commits, "score": gh.developer_score}}


# --- MODULE F4: Job Platform Connector ---
@router.get("/jobs/sync")
def sync_external_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock fetching jobs from Indeed/LinkedIn APIs
    return [
        {"title": "Cloud Architect", "company": "Amazon AWS", "source": "LinkedIn", "salary": "$180k"},
        {"title": "Senior DevOps Engineer", "company": "Google Cloud", "source": "Indeed", "salary": "$170k"}
    ]

@router.post("/jobs/apply")
def apply_to_job(req: JobApplyReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    app = JobApplication(
        user_id=current_user.id,
        company_name=req.company_name,
        job_title=req.job_title,
        source=req.source
    )
    db.add(app)
    db.commit()
    return {"message": "Application tracked via connector"}


# --- MODULE F5: Calendar & Scheduling ---
@router.post("/calendar/schedule")
def schedule_event(req: ScheduleReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = CalendarEvent(
        user_id=current_user.id,
        title=req.title,
        start_time=datetime.fromisoformat(req.date.replace("Z", "+00:00")),
        meeting_link="https://meet.google.com/mock-link"
    )
    db.add(event)
    db.commit()
    return {"message": "Event scheduled in Google Calendar", "link": event.meeting_link}

@router.get("/calendar/events")
def get_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    events = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id).all()
    return events


# --- MODULE F6: Email & Communication ---
@router.get("/email/logs")
def get_email_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(EmailLog).filter(EmailLog.user_id == current_user.id).all()
    if not logs:
        # Generate mock logs
        log1 = EmailLog(user_id=current_user.id, subject="Welcome to ResumeSphere Cloud", status="Delivered")
        log2 = EmailLog(user_id=current_user.id, subject="Weekly Career Report", status="Sent")
        db.add(log1)
        db.add(log2)
        db.commit()
        logs = [log1, log2]
    return logs


# --- MODULE F7: Public API Platform ---
@router.post("/developer/keys")
def generate_api_key(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    key = ApiKey(user_id=current_user.id, key=f"rs_{uuid.uuid4().hex}")
    db.add(key)
    db.commit()
    return {"api_key": key.key}

@router.post("/developer/webhooks")
def register_webhook(req: WebhookReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    hook = Webhook(user_id=current_user.id, url=req.url, event_type=req.event_type)
    db.add(hook)
    db.commit()
    return {"message": "Webhook registered"}


# --- MODULE F8: AI Automation Engine ---
def run_automation_background(task_name: str, user_id: str, db: Session):
    # Simulate long running automation (e.g. Weekly Review Generation)
    time.sleep(2)
    # Log email
    log = EmailLog(user_id=user_id, subject=f"Automation Complete: {task_name}", status="Delivered")
    db.add(log)
    db.commit()

@router.post("/automation/execute")
def trigger_automation(req: AutomationReq, bg_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(AutomationTask).filter(AutomationTask.user_id == current_user.id, AutomationTask.task_name == req.task_name).first()
    if not task:
        task = AutomationTask(user_id=current_user.id, task_name=req.task_name)
        db.add(task)
    task.last_run = datetime.utcnow()
    db.commit()
    
    bg_tasks.add_task(run_automation_background, req.task_name, current_user.id, db)
    return {"message": f"Automation '{req.task_name}' dispatched to background workers."}

@router.get("/automation/tasks")
def list_automations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(AutomationTask).filter(AutomationTask.user_id == current_user.id).all()


# --- MODULE F9: Observability & Monitoring ---
@router.get("/system/metrics")
def get_system_metrics(db: Session = Depends(get_db), current_user: User = Depends(requires_role(["Admin", "HR", "Recruiter", "Candidate"]))):
    # Generating real-time mock metrics
    return {
        "api_latency_ms": random.uniform(20.0, 150.0),
        "memory_usage_mb": random.uniform(250.0, 500.0),
        "active_connections": random.randint(50, 200),
        "db_query_time_ms": random.uniform(2.0, 15.0),
        "error_rate_percent": random.uniform(0.01, 0.5)
    }
