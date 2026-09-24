# Cyber Security Risk Predictor

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework](https://img.shields.io/badge/Web-Flask%20%2F%20FastAPI-green.svg)](https://flask.palletsprojects.com/)

An end-to-end machine learning and web application platform designed to evaluate, assess, and predict cybersecurity risk levels based on key threat indicators, infrastructure vulnerability metrics, and security operational logs.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Project Architecture](#project-architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Web Application & API](#web-application--api)
  - [Running the Web Server](#running-the-web-server)
  - [API Endpoints](#api-endpoints)
- [Machine Learning Pipeline](#machine-learning-pipeline)
  - [Training](#training)
  - [Batch Inference](#batch-inference)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

Modern organizations face rapidly evolving digital threat landscapes. **Cyber Security Risk Predictor** bridges predictive machine learning with an interactive web platform and REST API. It ingests system metrics, exploitability indices, and historical breach signals to classify risk severity (Low, Medium, High, Critical), enabling proactive threat triage.

---

## Key Features

- **End-to-End ML Pipeline**: Modular data cleaning, feature engineering, and model inference pipelines.
- **Multi-Class Risk Scoring**: Categorizes infrastructure risk into distinct operational severity tiers.
- **Interactive Web Interface**: Clean UI built with server-rendered templates, real-time input forms, and risk distribution visualizers.
- **RESTful API Services**: JSON-based endpoints enabling external security tools and CI/CD pipelines to query predictions programmatically.
- **Model Explainability & Metrics**: Tracks feature importances, ROC-AUC, Precision, and Recall scores.

---

## Project Architecture

```text
Cyber_Security_risk_predictor/
│
├── cyber-risk-predictor/
│   ├── data/                 # Raw and processed datasets
│   │   ├── raw/
│   │   └── processed/
│   │
│   ├── notebooks/            # Jupyter notebooks for EDA and experimentation
│   │   └── model_exploration.ipynb
│   │
│   ├── models/               # Serialized model artifacts & scalers
│   │   ├── risk_classifier.pkl
│   │   └── scaler.pkl
│   │
│   ├── src/                  # Core machine learning pipelines
│   │   ├── __init__.py
│   │   ├── preprocess.py     # Cleaning, normalization, and encoding
│   │   ├── train.py          # Model training and artifact generation
│   │   └── predict.py        # Model loading and inference functions
│   │
│   ├── web/                  # Web dashboard and API backend
│   │   ├── app.py            # Main server entrypoint
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── api.py        # REST endpoints for model inference
│   │   │   └── views.py      # Front-end UI page controllers
│   │   ├── templates/        # Jinja2 HTML templates
│   │   │   ├── base.html     # Global page layout
│   │   │   ├── index.html    # Risk assessment input form
│   │   │   └── result.html   # Prediction scorecard and charts
│   │   └── static/           # Static frontend assets
│   │       ├── css/
│   │       │   └── styles.css
│   │       ├── js/
│   │       │   └── charts.js
│   │       └── img/
│   │           └── logo.svg
│   │
│   ├── tests/                # Unit tests for models and routes
│   │   ├── test_pipeline.py
│   │   └── test_api.py
│   │
│   ├── Dockerfile            # Container deployment specification
│   └── requirements.txt      # Python dependencies
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- `pip` package manager
- (Optional) Git and virtualenv

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Arman2312/Cyber_Security_risk_predictor.git
   cd Cyber_Security_risk_predictor/cyber-risk-predictor
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # macOS / Linux:
   python3 -m venv venv
   source venv/bin/activate

   # Windows:
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Web Application & API

### Running the Web Server

From the `cyber-risk-predictor` root directory, launch the web application:

```bash
# Option 1: Directly run the app script
python web/app.py

# Option 2: Run via Flask CLI
export FLASK_APP=web/app.py
flask run --host=0.0.0.0 --port=5000
```

Once running, access the dashboard at:
```text
http://localhost:5000
```

---

### API Endpoints

The web backend exposes RESTful endpoints for programmatic integration:

#### 1. System Health Check
- **Endpoint:** `GET /api/v1/health`
- **Description:** Verifies service uptime and loaded model status.
- **Sample Response:**
  ```json
  {
    "status": "healthy",
    "model_loaded": true,
    "version": "1.0.0"
  }
  ```

#### 2. Risk Prediction
- **Endpoint:** `POST /api/v1/predict`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "cvss_score": 8.4,
    "patch_latency_days": 42,
    "open_ports_count": 14,
    "failed_logins_24h": 320,
    "endpoint_edr_active": 0,
    "data_criticality_level": 3
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "risk_level": "High",
    "risk_score": 0.86,
    "confidence": 0.91,
    "recommendations": [
      "Immediate patch application recommended for high-scoring CVSS CVEs.",
      "Enable EDR monitoring on unmanaged endpoints.",
      "Enforce IP lockouts on brute-force login targets."
    ]
  }
  ```

#### 3. Batch Risk Assessment
- **Endpoint:** `POST /api/v1/predict/batch`
- **Request Body:** Array of system feature records.
- **Response:** Array of risk classification objects.

---

## Machine Learning Pipeline

### Training

To clean raw datasets, engineer features, and train the predictive classifier:

```bash
python src/train.py --data-path data/raw/threat_data.csv --output-dir models/
```

### Batch Inference

To run standalone batch scoring over a CSV dataset without running the web UI:

```bash
python src/predict.py --input-path data/raw/test_hosts.csv --output-path data/processed/predictions.csv
```

---

## Tech Stack

- **Machine Learning & Data Processing:** Scikit-learn, XGBoost, Pandas, NumPy
- **Backend & Web Framework:** Flask / FastAPI, Jinja2
- **Frontend Assets:** HTML5, CSS3, JavaScript, Chart.js
- **Model Persistence:** Joblib, Pickle
- **Testing:** Pytest

---

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/ThreatModelUpdate`).
3. Commit your changes (`git commit -m 'Add support for cloud audit logs'`).
4. Push to the branch (`git push origin feature/ThreatModelUpdate`).
5. Open a Pull Request.

---

## License

Distributed under the MIT License. See `LICENSE` for details.

---

## Author

- **Arman** - [@Arman2312](https://github.com/Arman2312)
