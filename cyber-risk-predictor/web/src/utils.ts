import type { RiskTier } from './types'

export const tierConfig: Record<RiskTier, {
  label: string
  color: string
  bg: string
  border: string
  glow: string
  icon: string
}> = {
  LOW: {
    label: 'LOW',
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.1)',
    border: 'rgba(16, 185, 129, 0.3)',
    glow: 'rgba(16, 185, 129, 0.2)',
    icon: 'shield-check',
  },
  MEDIUM: {
    label: 'MEDIUM',
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.1)',
    border: 'rgba(245, 158, 11, 0.3)',
    glow: 'rgba(245, 158, 11, 0.2)',
    icon: 'shield-alert',
  },
  CRITICAL: {
    label: 'CRITICAL',
    color: '#ef4444',
    bg: 'rgba(239, 68, 68, 0.1)',
    border: 'rgba(239, 68, 68, 0.3)',
    glow: 'rgba(239, 68, 68, 0.25)',
    icon: 'shield-x',
  },
}

export const impactLabels: Record<string, string> = {
  high_positive: 'High Risk Increase',
  moderate_positive: 'Moderate Risk Increase',
  low_positive: 'Low Risk Increase',
  neutral: 'Neutral',
  negative: 'Risk Decrease',
}

export const impactColors: Record<string, string> = {
  high_positive: '#ef4444',
  moderate_positive: '#f59e0b',
  low_positive: '#fbbf24',
  neutral: '#64748b',
  negative: '#10b981',
}

export function formatFeature(name: string): string {
  return name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export function formatTimestamp(ts: string): string {
  const d = new Date(ts)
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
