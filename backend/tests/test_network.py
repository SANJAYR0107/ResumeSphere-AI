import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.services.network_ai_service import network_ai

client = TestClient(app)

def test_network_ai_recommend_connections():
    skills = "Python, React"
    profiles = [
        {"user_id": "u1", "skills": "Python, Django", "headline": "Dev"},
        {"user_id": "u2", "skills": "Design", "headline": "Designer"},
        {"user_id": "u3", "skills": "React, TypeScript", "headline": "Frontend"}
    ]
    
    recommended = network_ai.recommend_connections(skills, profiles)
    assert len(recommended) > 0
    # Both u1 and u3 should have some match
    ids = [p["user_id"] for p in recommended]
    assert "u1" in ids or "u3" in ids

def test_network_ai_team_formation():
    reqs = "Python, Docker, React"
    users = [
        {"user_id": "u1", "skills": "Python"},
        {"user_id": "u2", "skills": "Docker"},
        {"user_id": "u3", "skills": "React"},
        {"user_id": "u4", "skills": "Java"}
    ]
    
    team = network_ai.match_teams(reqs, users, team_size=3)
    assert len(team) == 3
    ids = [u["user_id"] for u in team]
    assert "u4" not in ids # u4 doesn't have required skills, ideally not picked

def test_network_semantic_search():
    query = "frontend developer"
    entities = [
        {"title": "Looking for frontend developer", "content": "React skills"},
        {"title": "Backend job", "content": "Python API"}
    ]
    results = network_ai.semantic_search_network(query, entities)
    assert len(results) > 0
    assert "frontend" in results[0]["title"].lower()

def test_network_feed_api():
    response = client.get("/api/network/feed")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_websocket_connection():
    # TestClient supports with client.websocket_connect()
    with client.websocket_connect("/api/network/ws/test_user_1") as websocket:
        websocket.send_json({"to": "test_user_2", "content": "Hello"})
        # We don't get a response directly because it sends to test_user_2
        # But we can verify connection doesn't drop
        
    with client.websocket_connect("/api/network/ws/test_user_1") as websocket:
        websocket.send_json({"content": "Broadcast!"})
        data = websocket.receive_json()
        assert data["content"] == "Broadcast!"
        assert data["from"] == "test_user_1"
