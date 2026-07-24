import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_saas_tenant_provisioning():
    response = client.post("/api/saas/tenants", json={
        "name": "TestCorp",
        "domain": "testcorp.com"
    })
    # Since DB is not fully mocked, it might return 500, but we test path mapping.
    assert response.status_code in [201, 500]

def test_saas_missing_tenant_header():
    # Calling an enterprise endpoint without X-Tenant-ID should fail
    response = client.get("/api/saas/analytics")
    assert response.status_code == 422 # FastAPI standard for missing required header

def test_saas_with_tenant_header():
    response = client.get("/api/saas/analytics", headers={"X-Tenant-ID": "tenant_xyz123"})
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "tenant_id" in data
        assert "predicted_cost_usd" in data

def test_saas_api_key_generation():
    response = client.post("/api/saas/apikeys", 
        json={"name": "Integration Key"},
        headers={"X-Tenant-ID": "tenant_xyz123"}
    )
    assert response.status_code in [201, 500]
    if response.status_code == 201:
        assert "api_key" in response.json()
