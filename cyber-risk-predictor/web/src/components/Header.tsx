import { useEffect, useState } from 'react'
import { Activity, ShieldCheck, AlertTriangle, ShieldX, Cpu, Radio } from 'lucide-react'
import type { HealthResponse } from '../types'
import { api } from '../api'

export function Header({ eventCount, criticalCount }: { eventCount: number; criticalCount: number }) {
  const [health, setHealth] = useState<HealthResponse | null>(null)

  useEffect(() => {
    const check = () => api.health().then(setHealth).catch(() => setHealth(null))
    check()
    const id = setInterval(check, 5000)
    return () => clearInterval(id)
  }, [])

  const healthy = health?.model_loaded ?? false

  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">
          <Radio size={28} strokeWidth={1.5} />
        </div>
        <div className="header-titles">
          <h1>AuthRisk-LR</h1>
          <span className="header-subtitle">Real-Time Cyber Authentication Risk Engine</span>
        </div>
      </div>

      <div className="header-stats">
        <div className="stat-pill">
          <Cpu size={16} />
          <span className="stat-label">Model</span>
          <span className={`stat-value ${healthy ? 'ok' : 'err'}`}>
            {healthy ? 'ONLINE' : 'OFFLINE'}
          </span>
          <span className={`status-dot ${healthy ? 'ok' : 'err'}`} />
        </div>

        <div className="stat-pill">
          <Activity size={16} />
          <span className="stat-label">Events</span>
          <span className="stat-value">{eventCount}</span>
        </div>

        <div className="stat-pill critical">
          <ShieldX size={16} />
          <span className="stat-label">Critical</span>
          <span className="stat-value">{criticalCount}</span>
        </div>
      </div>

      <div className="header-indicators">
        <div className="indicator">
          <ShieldCheck size={14} />
          <span>ALLOW</span>
        </div>
        <div className="indicator warn">
          <AlertTriangle size={14} />
          <span>MFA</span>
        </div>
        <div className="indicator err">
          <ShieldX size={14} />
          <span>SUSPEND</span>
        </div>
      </div>
    </header>
  )
}
