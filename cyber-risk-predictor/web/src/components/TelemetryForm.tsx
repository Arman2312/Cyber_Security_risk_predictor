import { useState, type FormEvent } from 'react'
import { Send, RotateCcw, Zap } from 'lucide-react'
import type { TelemetryInput } from '../types'

interface Props {
  onSubmit: (data: TelemetryInput) => void
  loading: boolean
}

const defaultPayload: TelemetryInput = {
  event_id: '',
  user_id: '',
  failed_attempts_5m: 0,
  ip_reputation_score: 0.05,
  velocity_kmh: 15,
  is_tor_or_vpn: 0,
  country_mismatch: 0,
  hour_anomaly_score: 0.1,
  device_trust_score: 0.95,
}

const presets: { label: string; icon: typeof Zap; data: TelemetryInput }[] = [
  {
    label: 'Normal Login',
    icon: Zap,
    data: { ...defaultPayload, event_id: '', user_id: 'usr_normal' },
  },
  {
    label: 'Suspicious',
    icon: Zap,
    data: {
      event_id: '',
      user_id: 'usr_suspicious',
      failed_attempts_5m: 3,
      ip_reputation_score: 0.55,
      velocity_kmh: 150,
      is_tor_or_vpn: 0,
      country_mismatch: 0,
      hour_anomaly_score: 0.3,
      device_trust_score: 0.4,
    },
  },
  {
    label: 'Attack',
    icon: Zap,
    data: {
      event_id: '',
      user_id: 'usr_compromised',
      failed_attempts_5m: 12,
      ip_reputation_score: 0.92,
      velocity_kmh: 2200,
      is_tor_or_vpn: 1,
      country_mismatch: 1,
      hour_anomaly_score: 0.88,
      device_trust_score: 0.05,
    },
  },
]

function genId() {
  return `evt_${Math.random().toString(36).slice(2, 10)}`
}

export function TelemetryForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<TelemetryInput>(defaultPayload)

  const update = (key: keyof TelemetryInput, value: string | number) => {
    setForm((f) => ({ ...f, [key]: value }))
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const payload = { ...form, event_id: form.event_id || genId() }
    onSubmit(payload)
  }

  const applyPreset = (data: TelemetryInput) => {
    setForm({ ...data, event_id: genId() })
  }

  const reset = () => setForm({ ...defaultPayload, event_id: genId() })

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Authentication Telemetry Input</h2>
        <span className="panel-tag">7 features</span>
      </div>

      <div className="preset-row">
        {presets.map((p) => (
          <button
            key={p.label}
            type="button"
            className="preset-btn"
            onClick={() => applyPreset(p.data)}
          >
            {p.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="telemetry-form">
        <div className="form-row">
          <label>
            <span>Event ID</span>
            <input
              type="text"
              value={form.event_id}
              onChange={(e) => update('event_id', e.target.value)}
              placeholder="auto-generated"
            />
          </label>
          <label>
            <span>User ID</span>
            <input
              type="text"
              value={form.user_id}
              onChange={(e) => update('user_id', e.target.value)}
              placeholder="usr_..."
            />
          </label>
        </div>

        <div className="form-group">
          <label>
            <span>Failed Attempts (5m)</span>
            <input
              type="number"
              min={0}
              value={form.failed_attempts_5m}
              onChange={(e) => update('failed_attempts_5m', parseInt(e.target.value) || 0)}
            />
          </label>
          <label>
            <span>IP Reputation Score</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={form.ip_reputation_score}
              onChange={(e) => update('ip_reputation_score', parseFloat(e.target.value))}
            />
            <span className="range-val">{form.ip_reputation_score.toFixed(2)}</span>
          </label>
        </div>

        <div className="form-group">
          <label>
            <span>Velocity (km/h)</span>
            <input
              type="number"
              min={0}
              step={0.1}
              value={form.velocity_kmh}
              onChange={(e) => update('velocity_kmh', parseFloat(e.target.value) || 0)}
            />
          </label>
          <label>
            <span>Hour Anomaly Score</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={form.hour_anomaly_score}
              onChange={(e) => update('hour_anomaly_score', parseFloat(e.target.value))}
            />
            <span className="range-val">{form.hour_anomaly_score.toFixed(2)}</span>
          </label>
        </div>

        <div className="form-group">
          <label>
            <span>Device Trust Score</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={form.device_trust_score}
              onChange={(e) => update('device_trust_score', parseFloat(e.target.value))}
            />
            <span className="range-val">{form.device_trust_score.toFixed(2)}</span>
          </label>
        </div>

        <div className="toggle-row">
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.is_tor_or_vpn === 1}
              onChange={(e) => update('is_tor_or_vpn', e.target.checked ? 1 : 0)}
            />
            <span className="toggle-track">
              <span className="toggle-thumb" />
            </span>
            <span className="toggle-label">Tor / VPN Exit Node</span>
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.country_mismatch === 1}
              onChange={(e) => update('country_mismatch', e.target.checked ? 1 : 0)}
            />
            <span className="toggle-track">
              <span className="toggle-thumb" />
            </span>
            <span className="toggle-label">Country Mismatch</span>
          </label>
        </div>

        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={reset}>
            <RotateCcw size={16} /> Reset
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            <Send size={16} /> {loading ? 'Analyzing...' : 'Evaluate Risk'}
          </button>
        </div>
      </form>
    </div>
  )
}
