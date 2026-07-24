import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_security_headers_present():
    """Verify OWASP Top 10 Security Headers are injected via Middleware."""
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers
    
    assert "x-content-type-options" in headers
    assert headers["x-content-type-options"] == "nosniff"
    
    assert "x-frame-options" in headers
    assert headers["x-frame-options"] == "DENY"
    
    assert "x-xss-protection" in headers
    assert headers["x-xss-protection"] == "1; mode=block"
    
    assert "strict-transport-security" in headers

# In a real environment, we'd mock the request.client.host to test the Rate Limiter rejection (429).
# For now, we ensure standard endpoints still return 200/404 rather than 429 for normal IPs.
def test_rate_limiter_allows_normal_traffic():
    response = client.get("/api/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
