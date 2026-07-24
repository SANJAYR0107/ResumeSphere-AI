from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import logging

from ..db.database import get_db
from ..db.models import (
    User, Profile, Connection, Post, Comment, Reaction, Message, 
    Conversation, ConversationParticipant, Community, Event
)
from ..services.network_ai_service import network_ai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/network", tags=["Global Network"])

# --- WebSockets Connection Manager (In-Memory) ---
class ConnectionManager:
    def __init__(self):
        # Maps user_id -> List of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket User {user_id} connected.")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket User {user_id} disconnected.")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

    async def broadcast(self, message: str):
        for connections in self.active_connections.values():
            for connection in connections:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Simple echo for now, in reality parse JSON and route to specific user
            payload = json.loads(data)
            target_user_id = payload.get("to")
            msg = payload.get("content", "")
            
            # If target provided, route direct. Else broadcast.
            response = json.dumps({"from": user_id, "content": msg, "timestamp": datetime.utcnow().isoformat()})
            if target_user_id:
                await manager.send_personal_message(response, target_user_id)
            else:
                await manager.broadcast(response)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# --- Schemas ---

class PostCreate(BaseModel):
    author_id: str
    content: str
    media_url: Optional[str] = None
    post_type: str = "Update"

class ConnectionRequest(BaseModel):
    requester_id: str
    recipient_id: str

# --- REST APIs ---

@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(post_data: PostCreate, db: Session = Depends(get_db)):
    db_post = Post(**post_data.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.get("/feed")
def get_social_feed(limit: int = 50, db: Session = Depends(get_db)):
    # Returns latest posts globally (for MVP)
    return db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()

@router.post("/connect", status_code=status.HTTP_201_CREATED)
def request_connection(req: ConnectionRequest, db: Session = Depends(get_db)):
    conn = Connection(**req.model_dump())
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn

# --- AI APIs ---

@router.get("/ai/recommend-connections")
def recommend_connections(user_skills: str, db: Session = Depends(get_db)):
    # Mocking fetching all profiles for MVP
    profiles = [
        {"user_id": "u1", "skills": "Python, React, Node", "headline": "Full Stack Dev"},
        {"user_id": "u2", "skills": "Design, Figma", "headline": "UI/UX Designer"},
        {"user_id": "u3", "skills": "Python, Django", "headline": "Backend Engineer"}
    ]
    return network_ai.recommend_connections(user_skills, profiles)

@router.get("/ai/team-formation")
def match_team(requirements: str):
    available_users = [
        {"user_id": "u1", "skills": "React, TypeScript"},
        {"user_id": "u2", "skills": "Python, PostgreSQL"},
        {"user_id": "u3", "skills": "Figma, UI/UX"},
        {"user_id": "u4", "skills": "DevOps, Docker"}
    ]
    team = network_ai.match_teams(requirements, available_users, team_size=3)
    return {"team": team}
