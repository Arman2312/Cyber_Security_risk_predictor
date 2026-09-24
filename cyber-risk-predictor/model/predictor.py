"""
Inference Engine, Policy Derivation, and Log-Odds Explainability
AuthRisk-LR System (REQ-INF-1 through REQ-INF-4, NFR-PERF-2)
"""

import os
from typing import Dict, List, Tuple, Any, Optional
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

FEATURE_NAMES = [
    "failed_attempts_5m",
    "ip_reputation_score",
    "velocity_kmh",
    "is_tor_or_vpn",
    "country_mismatch",
    "hour_anomaly_score",
    "device_trust_score",
]


def classify_impact(c_i: float) -> str:
    """
    Categorize directional log-odds contribution into schema-defined impact enums:
    ["high_positive", "moderate_positive", "low_positive", "neutral", "negative"]
    """
    if c_i > 1.0:
        return "high_positive"
    elif c_i > 0.3:
        return "moderate_positive"
    elif c_i > 0.0001:
        return "low_positive"
    elif abs(c_i) <= 0.0001:
        return "neutral"
    else:
        return "negative"


class RiskPredictor:
    """
    Singleton risk inference engine deserializing model artifact once at startup.
    Fails closed if model is missing or invalid (NFR-REL-2).
    Optimized for sub-millisecond in-memory inference (NFR-PERF-2).
    """

    def __init__(self, model_path: str = "artifacts/model.joblib"):
        self.model_path = model_path
        self.pipeline: Optional[Pipeline] = None
        self.scaler: Optional[StandardScaler] = None
        self.classifier: Optional[LogisticRegression] = None
        self.mean_: Optional[np.ndarray] = None
        self.scale_: Optional[np.ndarray] = None
        self.weights_: Optional[np.ndarray] = None
        self.bias_: float = 0.0
        self.load_model()

    def load_model(self) -> None:
        """
        REQ-INF-1: Deserialize model artifact.
        NFR-REL-2: Raise fatal exception if artifact is missing, corrupted, or incompatible.
        """
        if not os.path.exists(self.model_path):
            raise RuntimeError(
                f"[NFR-REL-2 FAIL-CLOSED] Model artifact missing at '{self.model_path}'. "
                "Service cannot start without a verified model artifact."
            )

        try:
            self.pipeline = joblib.load(self.model_path)
            if not isinstance(self.pipeline, Pipeline):
                raise ValueError("Loaded artifact is not a valid scikit-learn Pipeline.")

            self.scaler = self.pipeline.named_steps.get("scaler")
            self.classifier = self.pipeline.named_steps.get("classifier")

            if self.scaler is None or self.classifier is None:
                raise ValueError("Pipeline missing 'scaler' or 'classifier' step.")

            # Cache vectorized parameters for sub-millisecond execution (NFR-PERF-2)
            self.mean_ = np.array(self.scaler.mean_, dtype=np.float64)
            self.scale_ = np.array(self.scaler.scale_, dtype=np.float64)
            self.weights_ = np.array(self.classifier.coef_[0], dtype=np.float64)
            self.bias_ = float(self.classifier.intercept_[0])

        except Exception as e:
            raise RuntimeError(
                f"[NFR-REL-2 FAIL-CLOSED] Failed to deserialize model artifact at '{self.model_path}': {e}"
            ) from e

    def predict(
        self,
        features: Dict[str, Any],
        low_threshold: float = 0.35,
        critical_threshold: float = 0.70,
    ) -> Tuple[float, str, str, List[Dict[str, str]], float]:
        """
        Compute inference probability, policy tier, action, and top 3 explainability factors.
        Returns:
            (risk_score, risk_tier, recommended_action, contributing_factors, raw_z)
        """
        # Fast array extraction conforming to deterministic feature order
        raw_vals = np.array([float(features[feat]) for feat in FEATURE_NAMES], dtype=np.float64)

        # REQ-INF-2: z-score standard scaling (mu=0, sigma=1)
        x_scaled = (raw_vals - self.mean_) / self.scale_

        # REQ-INF-2 & Appendix 7.1: Sigmoid calculation z = w^T * x + b, p = 1 / (1 + e^-z)
        z = float(self.bias_ + np.dot(self.weights_, x_scaled))
        p = 1.0 / (1.0 + np.exp(-z))
        risk_score = round(float(p), 4)

        # REQ-INF-3: Policy tier and action assignment
        if risk_score < low_threshold:
            risk_tier = "LOW"
            recommended_action = "ALLOW"
        elif risk_score < critical_threshold:
            risk_tier = "MEDIUM"
            recommended_action = "MFA_CHALLENGE"
        else:
            risk_tier = "CRITICAL"
            recommended_action = "SUSPEND_AND_ALERT"

        # REQ-INF-4 & Appendix 7.2: Directional log-odds contributions (c_i = w_i * x_{i, scaled})
        contributions = []
        for i, feat_name in enumerate(FEATURE_NAMES):
            c_i = float(self.weights_[i] * x_scaled[i])
            impact = classify_impact(c_i)
            contributions.append({
                "feature": feat_name,
                "c_i": c_i,
                "impact": impact,
            })

        # Sort descending by contribution c_i to prioritize top 3 risk-increasing factors
        contributions.sort(key=lambda item: item["c_i"], reverse=True)
        top_factors = [
            {"feature": item["feature"], "impact": item["impact"]}
            for item in contributions[:3]
        ]

        return risk_score, risk_tier, recommended_action, top_factors, z
