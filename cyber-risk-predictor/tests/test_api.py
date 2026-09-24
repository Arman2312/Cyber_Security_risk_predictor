"""
REST API Integration & Performance Benchmark Tests
AuthRisk-LR System (REQ-API-1..2, NFR-PERF-1, NFR-SEC-1, NFR-SEC-3, NFR-REL-2)
"""

import os
import time
import httpx
import numpy as np
import pytest
from starlette.testclient import TestClient

from api.config import settings
from api.main import create_app, lifespan
from data.generate_dataset import generate_synthetic_data
from model.predictor import RiskPredictor
from model.train import train_and_evaluate


@pytest.fixture(scope="session")
def setup_model():
    """Ensure a trained model artifact is ready before running API tests."""
    data_dir = os.path.join(settings.BASE_DIR, "data")
    artifacts_dir = os.path.join(settings.BASE_DIR, "artifacts")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)

    data_path = os.path.join(data_dir, "auth_telemetry.csv")
    if not os.path.exists(data_path):
        df = generate_synthetic_data(n_samples=5000, malicious_ratio=0.15, random_state=42)
        df.to_csv(data_path, index=False)

    if not os.path.exists(settings.MODEL_PATH) or not os.path.exists(settings.METADATA_PATH):
        train_and_evaluate(
            data_path=data_path,
            artifact_path=settings.MODEL_PATH,
            metadata_path=settings.METADATA_PATH,
        )


@pytest.fixture
def client(setup_model):
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_health_check(client):
    """Verify /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "timestamp" in data


def test_model_metadata(client):
    """Verify /model/metadata endpoint."""
    response = client.get("/model/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "coefficients" in data
    assert "intercept" in data
    assert "metrics" in data
    assert data["metrics"]["roc_auc"] >= 0.88


def test_predict_risk_low(client):
    """Verify valid low-risk prediction response schema and values."""
    payload = {
        "event_id": "evt_test_001",
        "user_id": "usr_normal_01",
        "failed_attempts_5m": 0,
        "ip_reputation_score": 0.05,
        "velocity_kmh": 15.0,
        "is_tor_or_vpn": 0,
        "country_mismatch": 0,
        "hour_anomaly_score": 0.1,
        "device_trust_score": 0.95,
    }
    response = client.post("/api/v1/predict-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "evt_test_001"
    assert data["risk_tier"] == "LOW"
    assert data["recommended_action"] == "ALLOW"
    assert 0.0 <= data["risk_score"] < 0.35
    assert len(data["contributing_factors"]) == 3
    assert "timestamp" in data


def test_predict_risk_medium(client):
    """Verify valid medium-risk prediction response and MFA_CHALLENGE action."""
    payload = {
        "event_id": "evt_test_medium",
        "user_id": "usr_medium_55",
        "failed_attempts_5m": 3,
        "ip_reputation_score": 0.55,
        "velocity_kmh": 150.0,
        "is_tor_or_vpn": 0,
        "country_mismatch": 0,
        "hour_anomaly_score": 0.3,
        "device_trust_score": 0.4,
    }
    response = client.post("/api/v1/predict-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "evt_test_medium"
    assert data["risk_tier"] == "MEDIUM"
    assert data["recommended_action"] == "MFA_CHALLENGE"
    assert 0.35 <= data["risk_score"] < 0.70
    assert len(data["contributing_factors"]) == 3


def test_predict_risk_critical(client):
    """Verify valid critical-risk prediction response schema and values."""
    payload = {
        "event_id": "evt_test_critical",
        "user_id": "usr_compromised_99",
        "failed_attempts_5m": 12,
        "ip_reputation_score": 0.92,
        "velocity_kmh": 2200.0,
        "is_tor_or_vpn": 1,
        "country_mismatch": 1,
        "hour_anomaly_score": 0.88,
        "device_trust_score": 0.05,
    }
    response = client.post("/api/v1/predict-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "evt_test_critical"
    assert data["risk_tier"] == "CRITICAL"
    assert data["recommended_action"] == "SUSPEND_AND_ALERT"
    assert data["risk_score"] >= 0.70
    assert len(data["contributing_factors"]) == 3


def test_boundary_validation_rejections(client):
    """Verify strict validation and rejection of out-of-boundary values (REQ-API-1)."""
    base_payload = {
        "event_id": "evt_invalid",
        "user_id": "usr_invalid",
        "failed_attempts_5m": 0,
        "ip_reputation_score": 0.1,
        "velocity_kmh": 10.0,
        "is_tor_or_vpn": 0,
        "country_mismatch": 0,
        "hour_anomaly_score": 0.1,
        "device_trust_score": 0.9,
    }

    # Test negative failed attempts
    bad1 = dict(base_payload, failed_attempts_5m=-2)
    assert client.post("/api/v1/predict-risk", json=bad1).status_code == 422

    # Test ip_reputation_score > 1.0
    bad2 = dict(base_payload, ip_reputation_score=1.5)
    assert client.post("/api/v1/predict-risk", json=bad2).status_code == 422

    # Test negative velocity
    bad3 = dict(base_payload, velocity_kmh=-100.0)
    assert client.post("/api/v1/predict-risk", json=bad3).status_code == 422

    # Test invalid enum for binary flag
    bad4 = dict(base_payload, is_tor_or_vpn=2)
    assert client.post("/api/v1/predict-risk", json=bad4).status_code == 422

    # Test parameter injection: unmapped JSON field (NFR-SEC-1)
    bad5 = dict(base_payload, malicious_extra_field="injection_attack")
    assert client.post("/api/v1/predict-risk", json=bad5).status_code == 422


def test_uninitialized_predictor(client):
    """Verify 503 response if predictor is uninitialized."""
    # Temporarily set predictor to None on running app
    original_predictor = client.app.state.predictor
    try:
        client.app.state.predictor = None
        payload = {
            "event_id": "evt_test",
            "user_id": "usr_test",
            "failed_attempts_5m": 0,
            "ip_reputation_score": 0.1,
            "velocity_kmh": 10.0,
            "is_tor_or_vpn": 0,
            "country_mismatch": 0,
            "hour_anomaly_score": 0.1,
            "device_trust_score": 0.9,
        }
        resp = client.post("/api/v1/predict-risk", json=payload)
        assert resp.status_code == 503
        assert "not initialized" in resp.json()["detail"]
    finally:
        client.app.state.predictor = original_predictor


def test_missing_metadata_file(client, monkeypatch):
    """Verify 404 response when metadata file does not exist."""
    monkeypatch.setattr(settings, "METADATA_PATH", "non_existent_metadata.json")
    resp = client.get("/model/metadata")
    assert resp.status_code == 404


def test_error_sanitization_no_stack_trace_leak(client, monkeypatch):
    """NFR-SEC-3: Verify unhandled internal exceptions do not leak stack traces or system paths."""
    def buggy_predict(*args, **kwargs):
        raise ValueError("Critical internal logic failure at /secure/internal/path")

    predictor = client.app.state.predictor
    monkeypatch.setattr(predictor, "predict", buggy_predict)

    payload = {
        "event_id": "evt_err",
        "user_id": "usr_err",
        "failed_attempts_5m": 0,
        "ip_reputation_score": 0.1,
        "velocity_kmh": 10.0,
        "is_tor_or_vpn": 0,
        "country_mismatch": 0,
        "hour_anomaly_score": 0.1,
        "device_trust_score": 0.9,
    }
    resp = client.post("/api/v1/predict-risk", json=payload)
    assert resp.status_code == 500
    # Must NOT leak exception details or file paths
    assert "/secure/internal/path" not in resp.text
    assert "Traceback" not in resp.text
    assert "detail" in resp.json()


@pytest.mark.anyio
async def test_lifespan_fail_closed(monkeypatch):
    """NFR-REL-2: Verify lifespan triggers SystemExit on missing model."""
    monkeypatch.setattr(settings, "MODEL_PATH", "missing_artifact.joblib")
    app = create_app()
    with pytest.raises(SystemExit) as exc_info:
        async with lifespan(app):
            pass
    assert exc_info.value.code == 1


@pytest.mark.anyio
async def test_latency_benchmark(setup_model):
    """
    NFR-PERF-1: Benchmark 1,000 batch requests benchmarked with httpx show p95 < 15ms.
    """
    app = create_app()
    app.state.predictor = RiskPredictor(model_path=settings.MODEL_PATH)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "event_id": "evt_bench",
            "user_id": "usr_bench",
            "failed_attempts_5m": 2,
            "ip_reputation_score": 0.35,
            "velocity_kmh": 80.0,
            "is_tor_or_vpn": 0,
            "country_mismatch": 0,
            "hour_anomaly_score": 0.25,
            "device_trust_score": 0.70,
        }

        # Warm-up (20 requests)
        for _ in range(20):
            await async_client.post("/api/v1/predict-risk", json=payload)

        latencies_ms = []
        # Benchmark 1,000 requests
        for _ in range(1000):
            t0 = time.perf_counter()
            resp = await async_client.post("/api/v1/predict-risk", json=payload)
            t1 = time.perf_counter()
            assert resp.status_code == 200
            latencies_ms.append((t1 - t0) * 1000.0)

        p95 = float(np.percentile(latencies_ms, 95))
        p50 = float(np.percentile(latencies_ms, 50))
        print(f"\n[NFR-PERF-1 Benchmark] 1,000 requests: p50={p50:.2f}ms, p95={p95:.2f}ms (Target < 15ms)")
        assert p95 < 15.0, f"p95 latency exceeded SLA: {p95:.2f}ms >= 15ms"
