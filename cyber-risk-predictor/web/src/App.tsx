import { useState, useCallback } from 'react'
import { Header } from './components/Header'
import { TelemetryForm } from './components/TelemetryForm'
import { RiskResult } from './components/RiskResult'
import { EventFeed } from './components/EventFeed'
import { ModelPanel } from './components/ModelPanel'
import { api } from './api'
import type { TelemetryInput, RiskPredictionResponse, EventLog } from './types'
import './App.css'

export default function App() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RiskPredictionResponse | null>(null)
  const [events, setEvents] = useState<EventLog[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async (payload: TelemetryInput) => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.predict(payload)
      setResult(res)
      setEvents((prev) =>
        [
          {
            event_id: res.event_id,
            user_id: payload.user_id,
            risk_score: res.risk_score,
            risk_tier: res.risk_tier,
            recommended_action: res.recommended_action,
            timestamp: res.timestamp,
          },
          ...prev,
        ].slice(0, 50),
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }, [])

  const criticalCount = events.filter((e) => e.risk_tier === 'CRITICAL').length

  return (
    <div className="app">
      <Header eventCount={events.length} criticalCount={criticalCount} />

      <main className="main-grid">
        <section className="col-left">
          <TelemetryForm onSubmit={handleSubmit} loading={loading} />
          {error && (
            <div className="error-banner">
              {error}
            </div>
          )}
          {result && <RiskResult result={result} />}
        </section>

        <section className="col-right">
          <ModelPanel />
          <EventFeed events={events} onClear={() => setEvents([])} />
        </section>
      </main>

      <footer className="footer">
        <span>AuthRisk-LR · L2-Regularized Logistic Regression · Sub-millisecond Inference</span>
      </footer>
    </div>
  )
}
