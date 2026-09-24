"""
Model & Data Pipeline Unit Tests
AuthRisk-LR System (REQ-DAT, REQ-ML, REQ-INF, NFR-REL-2)
"""

import os
import joblib
import pytest
import numpy as np
import pandas as pd
from data.generate_dataset import generate_synthetic_data
from model.train import build_pipeline, train_and_evaluate, FEATURE_NAMES, TARGET_COLUMN
from model.predictor import RiskPredictor, classify_impact


def test_synthetic_data_generation_constraints():
    """REQ-DAT-1, REQ-DAT-2, REQ-DAT-3: Verify synthetic dataset generation."""
    df = generate_synthetic_data(n_samples=1000, malicious_ratio=0.15, random_state=42)

    # REQ-DAT-2: 7 distinct features + 1 label
    assert set(FEATURE_NAMES).issubset(set(df.columns))
    assert TARGET_COLUMN in df.columns
    assert len(df) == 1000

    # REQ-DAT-3: Zero null, NaN, or non-numeric values
    assert df.isnull().sum().sum() == 0

    # Label distribution check
    malicious_rate = df[TARGET_COLUMN].mean()
    assert 0.10 <= malicious_rate <= 0.20

    # Range checks
    assert (df["failed_attempts_5m"] >= 0).all()
    assert (df["ip_reputation_score"] >= 0.0).all() and (df["ip_reputation_score"] <= 1.0).all()
    assert (df["velocity_kmh"] >= 0.0).all()
    assert set(df["is_tor_or_vpn"].unique()).issubset({0, 1})
    assert set(df["country_mismatch"].unique()).issubset({0, 1})
    assert (df["hour_anomaly_score"] >= 0.0).all() and (df["hour_anomaly_score"] <= 1.0).all()
    assert (df["device_trust_score"] >= 0.0).all() and (df["device_trust_score"] <= 1.0).all()


def test_training_pipeline_and_metrics(tmp_path):
    """REQ-ML-1 through REQ-ML-6: Verify training, evaluation, and serialization."""
    data_file = tmp_path / "test_data.csv"
    artifact_file = tmp_path / "model.joblib"
    metadata_file = tmp_path / "metadata.json"

    df = generate_synthetic_data(n_samples=2000, malicious_ratio=0.15, random_state=42)
    df.to_csv(data_file, index=False)

    pipeline, metadata = train_and_evaluate(
        data_path=str(data_file),
        artifact_path=str(artifact_file),
        metadata_path=str(metadata_file),
        test_size=0.20,
        random_state=42,
    )

    # Check artifacts exist
    assert artifact_file.exists()
    assert metadata_file.exists()

    # REQ-ML-6: Verify metrics thresholds
    assert metadata["metrics"]["roc_auc"] >= 0.88
    assert metadata["metrics"]["f1_score"] >= 0.80
    assert len(metadata["coefficients"]) == 7


def test_mathematical_equivalence_and_policy(tmp_path):
    """REQ-INF-2, REQ-INF-3, REQ-INF-4: Sigmoid equivalence, policy tiers, and factors."""
    data_file = tmp_path / "test_data.csv"
    artifact_file = tmp_path / "model.joblib"
    metadata_file = tmp_path / "metadata.json"

    df = generate_synthetic_data(n_samples=1000, malicious_ratio=0.15, random_state=42)
    df.to_csv(data_file, index=False)
    train_and_evaluate(str(data_file), str(artifact_file), str(metadata_file))

    predictor = RiskPredictor(model_path=str(artifact_file))

    # Low-risk sample (ALLOW)
    low_risk_sample = {
        "failed_attempts_5m": 0,
        "ip_reputation_score": 0.05,
        "velocity_kmh": 20.0,
        "is_tor_or_vpn": 0,
        "country_mismatch": 0,
        "hour_anomaly_score": 0.1,
        "device_trust_score": 0.95,
    }
    score, tier, action, factors, z = predictor.predict(low_risk_sample)
    assert tier == "LOW"
    assert action == "ALLOW"
    assert score < 0.35
    assert len(factors) == 3

    # Medium-risk sample (MFA_CHALLENGE)
    medium_risk_sample = {
        "failed_attempts_5m": 3,
        "ip_reputation_score": 0.55,
        "velocity_kmh": 150.0,
        "is_tor_or_vpn": 0,
        "country_mismatch": 0,
        "hour_anomaly_score": 0.3,
        "device_trust_score": 0.4,
    }
    score_m, tier_m, action_m, factors_m, z_m = predictor.predict(medium_risk_sample)
    assert tier_m == "MEDIUM"
    assert action_m == "MFA_CHALLENGE"
    assert 0.35 <= score_m < 0.70
    assert len(factors_m) == 3

    # High-risk sample (SUSPEND_AND_ALERT)
    high_risk_sample = {
        "failed_attempts_5m": 15,
        "ip_reputation_score": 0.95,
        "velocity_kmh": 2500.0,
        "is_tor_or_vpn": 1,
        "country_mismatch": 1,
        "hour_anomaly_score": 0.85,
        "device_trust_score": 0.05,
    }
    score_h, tier_h, action_h, factors_h, z_h = predictor.predict(high_risk_sample)
    assert tier_h == "CRITICAL"
    assert action_h == "SUSPEND_AND_ALERT"
    assert score_h >= 0.70
    assert len(factors_h) == 3


def test_fail_closed_on_missing_model():
    """NFR-REL-2: Verify system raises fatal exception when model is missing."""
    with pytest.raises(RuntimeError, match="FAIL-CLOSED"):
        RiskPredictor(model_path="non_existent_model_file.joblib")


def test_fail_closed_on_corrupted_model(tmp_path):
    """NFR-REL-2: Verify system raises fatal exception on invalid/corrupted artifact."""
    bad_artifact = tmp_path / "corrupted.joblib"
    # Write a dict instead of a Pipeline
    joblib.dump({"not_a": "pipeline"}, bad_artifact)
    with pytest.raises(RuntimeError, match="FAIL-CLOSED"):
        RiskPredictor(model_path=str(bad_artifact))

    # Write a Pipeline missing classifier step
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    bad_pipe = tmp_path / "missing_step.joblib"
    joblib.dump(Pipeline([("scaler", StandardScaler())]), bad_pipe)
    with pytest.raises(RuntimeError, match="FAIL-CLOSED"):
        RiskPredictor(model_path=str(bad_pipe))


def test_training_pipeline_error_conditions(tmp_path):
    """Verify train_and_evaluate error handling on invalid input datasets."""
    # Non-existent dataset
    with pytest.raises(FileNotFoundError):
        train_and_evaluate("non_existent.csv")

    # Missing columns
    bad_csv = tmp_path / "bad.csv"
    pd.DataFrame({"failed_attempts_5m": [1]}).to_csv(bad_csv, index=False)
    with pytest.raises(ValueError, match="missing required columns"):
        train_and_evaluate(str(bad_csv))


def test_classify_impact():
    assert classify_impact(1.5) == "high_positive"
    assert classify_impact(0.5) == "moderate_positive"
    assert classify_impact(0.1) == "low_positive"
    assert classify_impact(0.0) == "neutral"
    assert classify_impact(-0.5) == "negative"
