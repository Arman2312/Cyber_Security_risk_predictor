import type { TelemetryInput, RiskPredictionResponse, ModelMetadata, HealthResponse } from './types'

const BASE = import.meta.env.VITE_API_URL || ''

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => fetchJSON<HealthResponse>('/health'),
  metadata: () => fetchJSON<ModelMetadata>('/model/metadata'),
  predict: (payload: TelemetryInput) =>
    fetchJSON<RiskPredictionResponse>('/api/v1/predict-risk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
}
