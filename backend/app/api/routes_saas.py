from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import logging

from ..db.database import get_db
from ..db.models import (
    Tenant, TenantSettings, Subscription, ApiCredential,
    AuditEvent, UsageRecord, ComplianceRecord
)
from ..services.saas_ai_service import saas_ai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/saas", tags=["Enterprise SaaS Platform"])

# --- Multi-Tenant Dependency (Conceptual Middleware) ---
def get_tenant_id(x_tenant_id: str = Header(..., description="Enterprise Tenant ID")) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is missing.")
    return x_tenant_id

# --- Schemas ---
class TenantCreate(BaseModel):
    name: str
    domain: Optional[str] = None

class SubscriptionCreate(BaseModel):
    plan_name: str
    
class ApiKeyCreate(BaseModel):
    name: str

# --- Tenants ---
@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def provision_tenant(req: TenantCreate, db: Session = Depends(get_db)):
    """Provisions a new Enterprise Workspace"""
    db_tenant = Tenant(name=req.name, domain=req.domain)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    # Init default settings
    db_settings = TenantSettings(tenant_id=db_tenant.id)
    db.add(db_settings)
    db.commit()
    
    return db_tenant

# --- Billing & Subscriptions ---
@router.post("/billing/subscribe")
def subscribe_tenant(
    req: SubscriptionCreate, 
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Mocks Stripe/Enterprise subscription"""
    sub = Subscription(
        tenant_id=tenant_id,
        plan_name=req.plan_name,
        current_period_end=datetime.utcnow() # would be +1 month normally
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

# --- Enterprise APIs ---
@router.post("/apikeys", status_code=status.HTTP_201_CREATED)
def generate_api_key(
    req: ApiKeyCreate, 
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    import uuid
    raw_key = f"rs_live_{uuid.uuid4().hex}"
    
    # Store hash only in prod, storing mock string for demo
    cred = ApiCredential(tenant_id=tenant_id, name=req.name, api_key_hash=raw_key)
    db.add(cred)
    db.commit()
    
    return {"name": req.name, "api_key": raw_key, "warning": "Store this securely. It will not be shown again."}

# --- AI Analytics & Compliance ---
@router.get("/analytics")
def get_tenant_analytics(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    # Fetch mock usage records
    usage = db.query(UsageRecord).filter(UsageRecord.tenant_id == tenant_id).all()
    records = [{"metric_name": u.metric_name, "quantity": u.quantity} for u in usage]
    
    # If empty, inject mock data to demonstrate AI
    if not records:
        records = [
            {"metric_name": "API_Call", "quantity": 15000},
            {"metric_name": "AI_Parse", "quantity": 850}
        ]
        
    return saas_ai.analyze_tenant_usage(tenant_id, records)

@router.get("/compliance")
def get_compliance_posture(
    tenant_id: str = Depends(get_tenant_id)
):
    return saas_ai.generate_compliance_report(tenant_id)
