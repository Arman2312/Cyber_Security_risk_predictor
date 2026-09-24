import { ShieldCheck, ShieldAlert, ShieldX, ArrowRight } from 'lucide-react'
import type { RiskPredictionResponse } from '../types'
import { tierConfig, impactLabels, impactColors, formatFeature } from '../utils'

const actionIcons = {
  ALLOW: ShieldCheck,
  MFA_CHALLENGE: ShieldAlert,
  SUSPEND_AND_ALERT: ShieldX,
}

export function RiskResult({ result }: { result: RiskPredictionResponse }) {
  const tier = tierConfig[result.risk_tier]
  const ActionIcon = actionIcons[result.recommended_action] || ShieldAlert
  const pct = result.risk_score * 100

  return (
    <div className="panel risk-result" style={{ animation: 'fade-in 0.3s ease' }}>
      <div className="panel-header">
        <h2>Risk Assessment</h2>
        <span className="panel-tag" style={{ color: tier.color, borderColor: tier.border, background: tier.bg }}>
          {tier.label}
        </span>
      </div>

      <div className="risk-display" style={{ '--tier-color': tier.color, '--tier-glow': tier.glow } as React.CSSProperties}>
        <div className="risk-gauge">
          <svg viewBox="0 0 200 120" className="gauge-svg">
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#1e293b" strokeWidth="12" strokeLinecap="round" />
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke={tier.color}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray="251.3"
              strokeDashoffset={251.3 - (251.3 * pct) / 100}
              style={{ transition: 'stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1)' }}
            />
          </svg>
          <div className="gauge-center">
            <span className="gauge-value" style={{ color: tier.color }}>
              {(result.risk_score * 100).toFixed(1)}%
            </span>
            <span className="gauge-label">Compromise Probability</span>
          </div>
        </div>

        <div className="risk-action" style={{ background: tier.bg, borderColor: tier.border }}>
          <div className="action-icon-wrap" style={{ color: tier.color }}>
            <ActionIcon size={32} strokeWidth={1.5} />
          </div>
          <div className="action-info">
            <span className="action-label">Recommended Action</span>
            <span className="action-value" style={{ color: tier.color }}>
              {result.recommended_action.replace(/_/g, ' ')}
            </span>
          </div>
          <ArrowRight size={20} style={{ color: tier.color }} />
        </div>
      </div>

      <div className="factors-section">
        <h3>Top Contributing Factors</h3>
        <div className="factors-list">
          {result.contributing_factors.map((f, i) => {
            const color = impactColors[f.impact] || '#64748b'
            return (
              <div
                key={f.feature}
                className="factor-item"
                style={{ animationDelay: `${i * 80}ms`, animation: 'slide-in 0.3s ease both', borderLeftColor: color }}
              >
                <div className="factor-rank">{i + 1}</div>
                <div className="factor-body">
                  <span className="factor-name">{formatFeature(f.feature)}</span>
                  <span className="factor-impact" style={{ color }}>
                    {impactLabels[f.impact] || f.impact}
                  </span>
                </div>
                <div className="factor-bar-wrap">
                  <div
                    className="factor-bar"
                    style={{
                      background: color,
                      width: f.impact === 'negative' ? '20%' : f.impact === 'neutral' ? '5%' : `${60 - i * 15}%`,
                      opacity: 0.7,
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="result-meta">
        <span>Event: <code>{result.event_id}</code></span>
        <span>Timestamp: {result.timestamp}</span>
      </div>
    </div>
  )
}
