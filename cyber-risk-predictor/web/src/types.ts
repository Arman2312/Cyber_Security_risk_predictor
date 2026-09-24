export interface TelemetryInput {
  event_id: string
  user_id: string
  failed_attempts_5m: number
  ip_reputation_score: number
  velocity_kmh: number
  is_tor_or_vpn: number
  country_mismatch: number
  hour_anomaly_score: number
  device_trust_score: number
}

export interface ContributingFactor {
  feature: string
  impact: string
}

export interface RiskPredictionResponse {
  event_id: string
  risk_score: number
  risk_tier: 'LOW' | 'MEDIUM' | 'CRITICAL'
  recommended_action: 'ALLOW' | 'MFA_CHALLENGE' | 'SUSPEND_AND_ALERT'
  contributing_factors: ContributingFactor[]
  timestamp: string
}

export interface ModelMetadata {
  model_version: string
  algorithm: string
  features: string[]
  intercept: number
  coefficients: Record<string, number>
  metrics: {
    roc_auc: number
    f1_score: number
    test_samples: number
  }
}

export interface HealthResponse {
  status: string
  model_loaded: boolean
  timestamp: string
}

export type RiskTier = 'LOW' | 'MEDIUM' | 'CRITICAL'

export interface EventLog {
  event_id: string
  user_id: string
  risk_score: number
  risk_tier: RiskTier
  recommended_action: string
  timestamp: string
}
