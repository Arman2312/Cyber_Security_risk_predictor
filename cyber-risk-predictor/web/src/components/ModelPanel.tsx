import { useEffect, useState } from 'react'
import { BarChart3, Target, GitBranch, TrendingUp } from 'lucide-react'
import type { ModelMetadata } from '../types'
import { api } from '../api'
import { formatFeature } from '../utils'

export function ModelPanel() {
  const [meta, setMeta] = useState<ModelMetadata | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    api.metadata().then(setMeta).catch(() => setError(true))
  }, [])

  if (error || !meta) {
    return (
      <div className="panel model-panel">
        <div className="panel-header">
          <h2><BarChart3 size={18} /> Model Intelligence</h2>
        </div>
        <div className="model-empty">Metadata unavailable</div>
      </div>
    )
  }

  const sortedCoefs = Object.entries(meta.coefficients).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
  const maxAbs = Math.max(...sortedCoefs.map(([, v]) => Math.abs(v)))

  return (
    <div className="panel model-panel">
      <div className="panel-header">
        <h2><BarChart3 size={18} /> Model Intelligence</h2>
        <span className="panel-tag">v{meta.model_version}</span>
      </div>

      <div className="model-metrics">
        <div className="metric-card">
          <Target size={18} />
          <div>
            <span className="metric-value">{meta.metrics.roc_auc.toFixed(4)}</span>
            <span className="metric-label">ROC-AUC</span>
          </div>
        </div>
        <div className="metric-card">
          <TrendingUp size={18} />
          <div>
            <span className="metric-value">{meta.metrics.f1_score.toFixed(4)}</span>
            <span className="metric-label">F1-Score</span>
          </div>
        </div>
        <div className="metric-card">
          <GitBranch size={18} />
          <div>
            <span className="metric-value">{meta.metrics.test_samples.toLocaleString()}</span>
            <span className="metric-label">Test Samples</span>
          </div>
        </div>
      </div>

      <div className="coef-section">
        <h3>Feature Coefficients (Log-Odds Weights)</h3>
        <div className="coef-list">
          {sortedCoefs.map(([name, val]) => {
            const pct = (Math.abs(val) / maxAbs) * 100
            const positive = val >= 0
            return (
              <div key={name} className="coef-row">
                <span className="coef-name">{formatFeature(name)}</span>
                <div className="coef-bar-wrap">
                  <div className="coef-bar-track">
                    <div
                      className="coef-bar"
                      style={{
                        width: `${pct}%`,
                        background: positive ? '#ef4444' : '#10b981',
                        marginLeft: positive ? '50%' : `${50 - pct}%`,
                      }}
                    />
                  </div>
                </div>
                <span className="coef-val" style={{ color: positive ? '#f87171' : '#34d399' }}>
                  {val >= 0 ? '+' : ''}{val.toFixed(3)}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      <div className="model-algo">
        <span className="algo-label">Algorithm</span>
        <span className="algo-value">{meta.algorithm}</span>
      </div>
    </div>
  )
}
