# Product Requirement Document (PRD)
## Project: Real-Time Cyber Authentication Risk Engine (AuthRisk-LR)

---

### 1. Executive Summary & Real-World Problem

#### 1.1 The Problem
Modern Security Operations Centers (SOCs) and Identity & Access Management (IAM) systems process thousands of access events every minute. Brute-force attacks, credential stuffing, and session hijackings account for over 60% of modern breach initial vectors. 

SOC analysts suffer from **alert fatigue**: standard rule-based triggers generate excessive false positives, while manual review cannot operate at login wire-speed.

#### 1.2 The Solution
A lightweight, backend-only microservice exposing a RESTful API powered by a calibrated **Logistic Regression model**. The service ingests real-time authentication telemetry (IP reputation, velocity/impossible travel, failed attempt frequency, geo-mismatch, UA entropy) and outputs:
1. A calibrated **Risk Probability Score** ($P(\text{Compromise}) \in [0.0, 1.0]$).
2. A deterministic **Action Tier** (`ALLOW`, `MFA_CHALLENGE`, `SUSPEND_AND_ALERT`).
3. An **Inference Explainability Object** (top feature contributions based on log-odds coefficients) satisfying compliance and SOC audit requirements.

#### 1.3 Why Logistic Regression?
* **Probabilistic Calibration:** Directly outputs well-calibrated posterior probabilities $P(Y=1 \mid X)$, essential for risk thresholds.
* **Sub-millisecond Latency:** Simple dot product $\sigma(\mathbf{w}^T \mathbf{x} + b)$ enables inline gating on auth gateways without adding user-perceptible delay ($< 5\text{ ms}$).
* **Explainability:** Feature weights (odds ratios) provide deterministic explanations to analysts without requiring black-box explainers (like SHAP).

---

### 2. Scope & Constraints

* **Scope:** Backend only (ML pipeline, serialization, REST API, automated testing, and synthetic realistic telemetry generator).
* **Out of Scope:** Frontend UI, distributed caching/Redis (in-memory rate window is sufficient for prototype), cloud deployment infrastructure.

---

### 3. System Architecture & Tech Stack

```
[ Client / Auth Gateway ]
           │
           │ HTTP POST /api/v1/predict-risk
           ▼
┌───────────────────────────────────────────────────────┐
│ FastAPI Backend Service                               │
│                                                       │
│   1. Request Validation (Pydantic v2)                 │
│   2. Preprocessing & Scaling (StandardScaler Pipeline)│
│   3. Inference Engine (scikit-learn LogisticRegression│
│   4. Explainability & Risk Threshold Policy Engine    │
└───────────────────────────────────────────────────────┘
           │
           ▼
  { JSON Response: risk_score, risk_level, top_factors }
```

#### Tech Stack
* **Language:** Python 3.10+
* **ML Core:** `scikit-learn`, `numpy`, `pandas`
* **API Framework:** `FastAPI`, `uvicorn`
* **Data Validation:** `pydantic`
* **Serialization:** `joblib`
* **Testing:** `pytest`, `httpx`

---

### 4. Machine Learning & Feature Specification

#### 4.1 Feature Vector ($\mathbf{x}$)
The model consumes 7 standardized features per event:

| Feature Name | Type | Description | Expected Range |
| :--- | :--- | :--- | :--- |
| `failed_attempts_5m` | Integer | Failed password attempts within the last 5 minutes | $0 - 50+$ |
| `ip_reputation_score` | Float | External threat intelligence score (0 = clean, 1 = malicious) | $0.0 - 1.0$ |
| `velocity_kmh` | Float | Calculated geographic speed from previous login location | $0.0 - 5000.0+$ |
| `is_tor_or_vpn` | Binary | Known exit node or proxy indicator | $0$ or $1$ |
| `country_mismatch` | Binary | User country differs from primary registered home country | $0$ or $1$ |
| `hour_anomaly_score` | Float | Deviation from user's historical access hours | $0.0 - 1.0$ |
| `device_trust_score` | Float | Device fingerprint validity (1 = trusted/enrolled, 0 = unknown) | $0.0 - 1.0$ |

#### 4.2 Mathematical Formulation
The log-odds of a malicious authentication attempt are modeled as:

$$\ln\left(\frac{p}{1 - p}\right) = \beta_0 + \sum_{i=1}^{n} \beta_i x_i$$

Prediction probability:

$$p = \sigma(\mathbf{w}^T \mathbf{x} + b) = \frac{1}{1 + e^{-(\mathbf{w}^T \mathbf{x} + b)}}$$

#### 4.3 Training & Regularization
* **Algorithm:** Logistic Regression with L2 regularization (`Ridge`) to prevent overfitting on collinear network features.
* **Loss Function:** Binary Cross-Entropy (Log Loss).
* **Class Imbalance Handling:** `class_weight='balanced'` to account for attacks being less frequent than legitimate logins.
