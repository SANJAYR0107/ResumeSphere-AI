from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import logging

from ..db.database import get_db
from ..db.models import (
    Plugin, PluginInstallation, Workflow, WorkflowExecution,
    Function, FunctionExecution, ModelRegistry
)
from ..services.platform_ai_service import platform_ai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["AI Operating System"])

# --- Schemas ---
class PluginCreate(BaseModel):
    name: str
    developer: str
    version: str
    description: str
    manifest: Dict[str, Any]

class WorkflowExecute(BaseModel):
    workflow_id: str
    payload: Dict[str, Any] = {}

class FunctionRun(BaseModel):
    code: str
    runtime: str = "python3.10"
    args: Dict[str, Any] = {}

class BIQuery(BaseModel):
    query: str

# --- App Ecosystem (Plugins) ---
@router.post("/plugins", status_code=status.HTTP_201_CREATED)
def register_plugin(req: PluginCreate, db: Session = Depends(get_db)):
    """Registers a new 3rd-party micro-app in the OS App Store."""
    db_plugin = Plugin(
        name=req.name,
        developer=req.developer,
        version=req.version,
        description=req.description,
        manifest=json.dumps(req.manifest)
    )
    db.add(db_plugin)
    db.commit()
    db.refresh(db_plugin)
    return db_plugin

@router.get("/plugins")
def list_plugins(db: Session = Depends(get_db)):
    """Lists available plugins in the marketplace."""
    return db.query(Plugin).all()

@router.post("/plugins/{plugin_id}/install")
def install_plugin(plugin_id: str, tenant_id: str, db: Session = Depends(get_db)):
    """Installs a plugin into a specific tenant workspace."""
    install = PluginInstallation(plugin_id=plugin_id, tenant_id=tenant_id, config="{}")
    db.add(install)
    db.commit()
    return {"status": "Installed", "plugin_id": plugin_id, "tenant_id": tenant_id}

# --- Workflow Engine ---
@router.post("/workflows/execute")
def execute_workflow(req: WorkflowExecute, db: Session = Depends(get_db)):
    """Triggers an Agentic workflow DAG."""
    workflow = db.query(Workflow).filter(Workflow.id == req.workflow_id).first()
    if not workflow:
        # Mock successful dispatch if no DB record found (for MVP frontend testing)
        return platform_ai.orchestrate_workflow('{"nodes": ["A", "B"]}')
        
    return platform_ai.orchestrate_workflow(workflow.definition)

# --- Custom Functions (Serverless Sandbox Mock) ---
@router.post("/functions/run")
def run_custom_function(req: FunctionRun):
    """Executes a custom function. Mocked to prevent arbitrary code execution."""
    return {
        "status": "Success",
        "runtime": req.runtime,
        "message": "Custom function execution mocked for security.",
        "logs": ["Initializing sandbox...", "Executing handler...", "Return 0"]
    }

# --- Business Intelligence ---
@router.post("/bi/query")
def run_bi_query(req: BIQuery):
    """Translates natural language to SQL and executes against the Data Warehouse."""
    return platform_ai.generate_sql_from_nl(req.query)
