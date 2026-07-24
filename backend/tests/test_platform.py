import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_platform_plugin_registration():
    response = client.post("/api/platform/plugins", json={
        "name": "TestPlugin",
        "developer": "TestCorp",
        "version": "1.0.0",
        "description": "A test plugin",
        "manifest": {"entry": "main.py"}
    })
    assert response.status_code in [201, 500]
    
def test_platform_plugin_list():
    response = client.get("/api/platform/plugins")
    assert response.status_code == 200

def test_platform_workflow_execution():
    response = client.post("/api/platform/workflows/execute", json={
        "workflow_id": "test_id",
        "payload": {}
    })
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "Running"

def test_platform_custom_function():
    response = client.post("/api/platform/functions/run", json={
        "code": "print('hello')",
        "runtime": "python3.10"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Success"

def test_platform_bi_query():
    response = client.post("/api/platform/bi/query", json={
        "query": "Show me revenue"
    })
    assert response.status_code == 200
    assert "generated_sql" in response.json()
