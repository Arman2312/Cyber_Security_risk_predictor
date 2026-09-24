"""
Model Training & Evaluation Pipeline
AuthRisk-LR System (REQ-ML-1 through REQ-ML-6)
"""

import argparse
import json
import os
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "failed_attempts_5m",
    "ip_reputation_score",
    "velocity_kmh",
    "is_tor_or_vpn",
    "country_mismatch",
    "hour_anomaly_score",
    "device_trust_score",
]

TARGET_COLUMN = "is_compromised"


def build_pipeline(random_state: int = 42) -> Pipeline:
    """
    Construct unified scikit-learn Pipeline with StandardScaler and L2 Logistic Regression.
    REQ-ML-2: Standard z-score normalization via StandardScaler.
    REQ-ML-3: L2-regularized Logistic Regression optimizing Binary Cross-Entropy loss.
    REQ-ML-4: class_weight='balanced' to handle minority attack distribution.
    """
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    solver="lbfgs",
                    class_weight="balanced",
                    random_state=random_state,
                    max_iter=1000,
                ),
            ),
        ]
    )


def train_and_evaluate(
    data_path: str,
    artifact_path: str = "artifacts/model.joblib",
    metadata_path: str = "artifacts/model_metadata.json",
    test_size: float = 0.20,
    random_state: int = 42,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Load data, execute train/test split (80/20), train pipeline, verify metrics,
    and serialize model artifact and metadata.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    df = pd.read_csv(data_path)
    
    # Validate columns
    missing_cols = set(FEATURE_NAMES + [TARGET_COLUMN]) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    X = df[FEATURE_NAMES]
    y = df[TARGET_COLUMN]

    # REQ-ML-1: 80% training split, 20% holdout test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    pipeline = build_pipeline(random_state=random_state)
    pipeline.fit(X_train, y_train)

    # Evaluate on test set
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    roc_auc = float(roc_auc_score(y_test, y_pred_proba))
    f1 = float(f1_score(y_test, y_pred))

    print(f"Test Set Evaluation Results:")
    print(f"ROC-AUC: {roc_auc:.4f} (Target >= 0.88)")
    print(f"F1-Score: {f1:.4f} (Target >= 0.80)")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # REQ-ML-6 verification
    if roc_auc < 0.88:
        raise AssertionError(f"Model failed REQ-ML-6: ROC-AUC {roc_auc:.4f} < 0.88")
    if f1 < 0.80:
        raise AssertionError(f"Model failed REQ-ML-6: F1-Score {f1:.4f} < 0.80")

    # Extract model coefficients and intercept for metadata / explainability
    lr_model: LogisticRegression = pipeline.named_steps["classifier"]
    coefficients = {
        name: float(weight)
        for name, weight in zip(FEATURE_NAMES, lr_model.coef_[0])
    }
    intercept = float(lr_model.intercept_[0])

    metadata = {
        "model_version": "1.0.0",
        "algorithm": "Ridge Logistic Regression (L2)",
        "features": FEATURE_NAMES,
        "intercept": intercept,
        "coefficients": coefficients,
        "metrics": {
            "roc_auc": round(roc_auc, 4),
            "f1_score": round(f1, 4),
            "test_samples": len(y_test),
        },
    }

    # REQ-ML-5: Persist pipeline artifact
    os.makedirs(os.path.dirname(os.path.abspath(artifact_path)), exist_ok=True)
    joblib.dump(pipeline, artifact_path)
    print(f"\nPersisted pipeline artifact -> {artifact_path}")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Persisted metadata -> {metadata_path}")

    return pipeline, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AuthRisk-LR machine learning pipeline.")
    parser.add_argument(
        "--data",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "data", "auth_telemetry.csv"),
        help="Path to training CSV dataset",
    )
    parser.add_argument(
        "--artifact",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "artifacts", "model.joblib"),
        help="Output model.joblib path",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "artifacts", "model_metadata.json"),
        help="Output metadata JSON path",
    )
    args = parser.parse_args()

    train_and_evaluate(args.data, args.artifact, args.metadata)
