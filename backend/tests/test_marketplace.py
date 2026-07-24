import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.services.marketplace_ai_service import marketplace_ai

client = TestClient(app)

def test_marketplace_ai_recommend_gigs():
    skills = "Python, React"
    gigs = [
        {"id": 1, "title": "Build a python script", "description": "data analysis"},
        {"id": 2, "title": "Design a logo", "description": "using photoshop"},
        {"id": 3, "title": "Develop react native app", "description": "mobile dev"}
    ]
    
    recommended = marketplace_ai.recommend_gigs(skills, gigs)
    # The scoring adds some randomness, but Python and React gigs should be present
    assert len(recommended) > 0
    ids = [g["id"] for g in recommended]
    assert 1 in ids or 3 in ids

def test_marketplace_ai_suggest_pricing():
    res = marketplace_ai.suggest_pricing("Development", "Python", "Expert")
    assert res["suggested_hourly_rate"] > 0
    assert "min_rate" in res
    assert "max_rate" in res

def test_marketplace_ai_trust_score():
    score = marketplace_ai.calculate_trust_score(total_completed_orders=10, average_rating=4.5, account_age_days=100)
    assert score > 0
    assert score <= 100

def test_marketplace_ai_fraud_detection():
    # High amount, low trust, new device -> should flag
    res = marketplace_ai.check_fraud(1500, 20, True)
    assert res["is_flagged"] is True
    
    # Low amount, high trust, old device -> should NOT flag
    res2 = marketplace_ai.check_fraud(50, 90, False)
    assert res2["is_flagged"] is False

def test_marketplace_analytics_api():
    # Tests the analytics endpoint
    response = client.get("/api/marketplace/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_gigs" in data
    assert "status" in data
    assert data["status"] == "Healthy"
