import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_latency_health_endpoint():
    """Benchmark: Health endpoint should return in under 50ms"""
    start_time = time.time()
    response = client.get("/api/health")
    duration_ms = (time.time() - start_time) * 1000
    
    assert response.status_code == 200
    assert duration_ms < 50.0, f"Health endpoint too slow: {duration_ms}ms"

def test_prometheus_metrics_exposed():
    """Ensure Prometheus metrics are generated rapidly"""
    start_time = time.time()
    response = client.get("/metrics")
    duration_ms = (time.time() - start_time) * 1000
    
    assert response.status_code == 200
    assert "app_uptime_seconds" in response.text
    assert "http_requests_total" in response.text
    assert duration_ms < 100.0, "Metrics generation is too slow"
