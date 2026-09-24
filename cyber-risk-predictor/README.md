# AuthRisk-LR: Real-Time Cyber Authentication Risk Engine

AuthRisk-LR is a high-throughput, low-latency backend microservice designed to sit inline with Identity and Access Management (IAM) systems and authentication gateways. It evaluates single-event authentication telemetry in real time, computes calibrated posterior probabilities of credential compromise using an $L_2$-regularized Logistic Regression model, enforces policy tiers (`ALLOW`, `MFA_CHALLENGE`, `SUSPEND_AND_ALERT`), and outputs deterministic log-odds feature attributions for SOC auditing.

---

## Architecture & Data Flow

```
[ Client / IdP / Auth Gateway ]
           │
           │ HTTP POST /api/v1/predict-risk
           ▼
┌────────────────────────────────────────────────────────┐
│ FastAPI Backend Microservice (Uvicorn ASGI)            │
│                                                        │
│  1. Strict Schema Validation (Pydantic v2)             │
│  2. Feature Standardization (StandardScaler Pipeline)   │
│  3. Calibrated Logistic Inference (σ(w^T x + b))       │
│  4. Policy Decision & Log-Odds Explainability Engine   │
└────────────────────────────────────────────────────────┘
           │
           ▼
  { risk_score, risk_tier, recommended_action, contributing_factors }
```

---

## Project Structure

```
cyber-risk-predictor/
├── requirements.txt           # Verified dependencies (Python 3.10+)
├── README.md                  # System documentation & usage guide
├── data/
│   ├── generate_dataset.py    # Deterministic synthetic telemetry generator (REQ-DAT)
│   └── auth_telemetry.csv     # Generated training/evaluation dataset
├── model/
│   ├── train.py               # Pipeline fitting, evaluation, and serialization (REQ-ML)
│   └── predictor.py           # In-memory inference engine & explainability (REQ-INF)
├── api/
│   ├── config.py              # Environment variable configurations (NFR-MNT-3)
│   ├── schemas.py             # Pydantic v2 models (REQ-API, NFR-SEC-1)
│   ├── routes.py              # REST API endpoint handlers
│   └── main.py                # ASGI application lifespan & error handling
├── artifacts/
│   ├── model.joblib           # Serialized scaler + logistic regression pipeline
│   └── model_metadata.json    # Coefficients, intercept, and evaluation metrics
└── tests/
    ├── test_model.py          # ML pipeline & mathematical equivalence tests
    └── test_api.py            # API integration & 1,000-request latency benchmark
```

---

## Quickstart Guide

### 1. Environment Setup & Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Generate Synthetic Dataset

Generates 10,000 records with 7 telemetry features and a 15% attack distribution:

```bash
python data/generate_dataset.py --samples 10000 --malicious-ratio 0.15 --seed 42
```

### 3. Train & Serialize the Model

Trains the $L_2$-regularized Logistic Regression pipeline, asserts $\text{ROC-AUC} \ge 0.88$ and $\text{F1-score} \ge 0.80$, and persists `artifacts/model.joblib`:

```bash
python model/train.py
```

### 4. Run Automated Test Suite & Coverage

```bash
pytest --cov=model --cov=api -v
```

### 5. Launch the REST API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## API Endpoints

### 1. Health Check
* **Endpoint:** `GET /health`
* **Response (HTTP 200):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2026-09-24T13:20:00Z"
}
```

### 2. Model Metadata
* **Endpoint:** `GET /model/metadata`
* **Response (HTTP 200):**
```json
{
  "model_version": "1.0.0",
  "algorithm": "Ridge Logistic Regression (L2)",
  "features": ["failed_attempts_5m", "ip_reputation_score", "velocity_kmh", "is_tor_or_vpn", "country_mismatch", "hour_anomaly_score", "device_trust_score"],
  "intercept": -1.245,
  "coefficients": { ... },
  "metrics": {
    "roc_auc": 1.0,
    "f1_score": 1.0,
    "test_samples": 2000
  }
}
```

### 3. Predict Risk
* **Endpoint:** `POST /api/v1/predict-risk`
* **Sample Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/predict-risk" \
     -H "Content-Type: application/json" \
     -d '{
       "event_id": "evt_98347294",
       "user_id": "usr_alpha_101",
       "failed_attempts_5m": 6,
       "ip_reputation_score": 0.82,
       "velocity_kmh": 1200.5,
       "is_tor_or_vpn": 1,
       "country_mismatch": 1,
       "hour_anomaly_score": 0.65,
       "device_trust_score": 0.10
     }'
```
* **Sample Response (HTTP 200):**
```json
{
  "event_id": "evt_98347294",
  "risk_score": 0.9998,
  "risk_tier": "CRITICAL",
  "recommended_action": "SUSPEND_AND_ALERT",
  "contributing_factors": [
    { "feature": "ip_reputation_score", "impact": "high_positive" },
    { "feature": "failed_attempts_5m", "impact": "high_positive" },
    { "feature": "velocity_kmh", "impact": "high_positive" }
  ],
  "timestamp": "2026-09-24T13:20:00Z"
}
```

---

## Policy Decision Matrix

| Risk Probability ($p$) | Tier | Recommended Action | Enforcement Description |
| :--- | :--- | :--- | :--- |
| $p < 0.35$ | `LOW` | `ALLOW` | Direct authorization granted without friction. |
| $0.35 \le p < 0.70$ | `MEDIUM` | `MFA_CHALLENGE` | Step-up challenge required (FIDO2 / OTP). |
| $p \ge 0.70$ | `CRITICAL` | `SUSPEND_AND_ALERT` | Immediate session rejection and SecOps alert trigger. |
