"""
Pydantic v2 Request & Response Schemas
AuthRisk-LR System (SRS 4.2 Data Formats & Schemas, NFR-SEC-1)
"""

from enum import Enum
from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict


class RiskTierEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


class RecommendedActionEnum(str, Enum):
    ALLOW = "ALLOW"
    MFA_CHALLENGE = "MFA_CHALLENGE"
    SUSPEND_AND_ALERT = "SUSPEND_AND_ALERT"


class FactorImpactEnum(str, Enum):
    HIGH_POSITIVE = "high_positive"
    MODERATE_POSITIVE = "moderate_positive"
    LOW_POSITIVE = "low_positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class ContributingFactor(BaseModel):
    feature: str
    impact: FactorImpactEnum


class TelemetryInput(BaseModel):
    """
    Input Telemetry Schema.
    NFR-SEC-1: Rejects any unmapped parameters (extra='forbid') to prevent parameter injection.
    """
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., description="Unique event identifier")
    user_id: str = Field(..., description="Target user identifier")
    failed_attempts_5m: int = Field(..., ge=0, description="Failed attempts in the last 5 minutes")
    ip_reputation_score: float = Field(..., ge=0.0, le=1.0, description="IP threat score [0.0, 1.0]")
    velocity_kmh: float = Field(..., ge=0.0, description="Calculated travel velocity in km/h")
    is_tor_or_vpn: Literal[0, 1] = Field(..., description="Known Tor/VPN exit flag (0 or 1)")
    country_mismatch: Literal[0, 1] = Field(..., description="Country mismatch flag (0 or 1)")
    hour_anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Access hour deviation [0.0, 1.0]")
    device_trust_score: float = Field(..., ge=0.0, le=1.0, description="Device fingerprint trust [0.0, 1.0]")


class RiskPredictionResponse(BaseModel):
    """
    Inference Response Schema conforming strictly to SRS 4.2.
    """
    event_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk probability rounded to 4 decimals")
    risk_tier: RiskTierEnum
    recommended_action: RecommendedActionEnum
    contributing_factors: List[ContributingFactor]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: str
