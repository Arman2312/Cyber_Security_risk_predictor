"""
REST API Route Handlers
AuthRisk-LR System (REQ-API-1, REQ-API-2, REQ-API-3)
"""

from datetime import datetime, timezone
import json
import os
from fastapi import APIRouter, HTTPException, Request, status
from api.config import settings
from api.schemas import HealthResponse, RiskPredictionResponse, TelemetryInput

router = APIRouter()


@router.post(
    "/api/v1/predict-risk",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute real-time authentication risk and policy action",
)
async def predict_risk(payload: TelemetryInput, request: Request):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Predictor engine is not initialized.",
        )

    risk_score, risk_tier, recommended_action, contributing_factors, _ = predictor.predict(
        payload.model_dump(),
        low_threshold=settings.LOW_RISK_THRESHOLD,
        critical_threshold=settings.CRITICAL_RISK_THRESHOLD,
    )

    utc_now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return RiskPredictionResponse(
        event_id=payload.event_id,
        risk_score=risk_score,
        risk_tier=risk_tier,
        recommended_action=recommended_action,
        contributing_factors=contributing_factors,
        timestamp=utc_now,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service health and model readiness check",
)
async def health_check(request: Request):
    predictor = getattr(request.app.state, "predictor", None)
    model_loaded = predictor is not None and predictor.pipeline is not None
    utc_now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        timestamp=utc_now,
    )


@router.get(
    "/model/metadata",
    status_code=status.HTTP_200_OK,
    summary="Expose model training metadata, coefficients, and evaluation metrics",
)
async def get_model_metadata():
    if not os.path.exists(settings.METADATA_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metadata is unavailable. Model may not have been trained yet.",
        )

    with open(settings.METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return metadata
