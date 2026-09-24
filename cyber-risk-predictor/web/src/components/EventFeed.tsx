import { Activity, Trash2 } from 'lucide-react'
import type { EventLog } from '../types'
import { tierConfig, formatTimestamp } from '../utils'

interface Props {
  events: EventLog[]
  onClear: () => void
}

export function EventFeed({ events, onClear }: Props) {
  return (
    <div className="panel event-feed-panel">
      <div className="panel-header">
        <h2>
          <Activity size={18} /> Live Event Stream
        </h2>
        {events.length > 0 && (
          <button className="clear-btn" onClick={onClear}>
            <Trash2 size={14} /> Clear
          </button>
        )}
      </div>

      <div className="event-feed">
        {events.length === 0 ? (
          <div className="feed-empty">
            <Activity size={32} />
            <p>No events evaluated yet. Submit telemetry to begin.</p>
          </div>
        ) : (
          events.map((evt, i) => {
            const tier = tierConfig[evt.risk_tier]
            return (
              <div
                key={`${evt.event_id}-${i}`}
                className="event-row"
                style={{
                  animation: 'slide-in 0.25s ease both',
                  borderLeftColor: tier.color,
                }}
              >
                <div className="event-dot" style={{ background: tier.color, boxShadow: `0 0 8px ${tier.glow}` }} />
                <div className="event-info">
                  <span className="event-user">{evt.user_id}</span>
                  <span className="event-id">{evt.event_id}</span>
                </div>
                <div className="event-score" style={{ color: tier.color }}>
                  {(evt.risk_score * 100).toFixed(1)}%
                </div>
                <div className="event-tier" style={{ background: tier.bg, color: tier.color, borderColor: tier.border }}>
                  {evt.risk_tier}
                </div>
                <div className="event-time">{formatTimestamp(evt.timestamp)}</div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
