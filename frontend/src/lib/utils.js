import { formatDistanceToNow, format } from 'date-fns'

export function riskColor(level) {
  return { critical: '#f87171', high: '#fbbf24', medium: '#60a5fa', low: '#4ade80' }[level] ?? '#94a3b8'
}

export function riskBadgeClass(level) {
  return `badge-${level ?? 'low'}`
}

export function severityBadgeClass(severity) {
  return `badge-${severity}`
}

export function formatTemp(v) {
  if (v == null) return '—'
  return `${Number(v).toFixed(1)}°C`
}

export function formatRH(v) {
  if (v == null) return '—'
  return `${Number(v).toFixed(1)}%`
}

export function formatEth(v) {
  if (v == null) return '—'
  return `${Number(v).toFixed(3)} ppm`
}

export function formatScore(v) {
  if (v == null) return '—'
  return `${Math.round(Number(v) * 100)}%`
}

export function timeAgo(ts) {
  if (!ts) return '—'
  try { return formatDistanceToNow(new Date(ts), { addSuffix: true }) }
  catch { return '—' }
}

export function shortTime(ts) {
  if (!ts) return ''
  try { return format(new Date(ts), 'HH:mm') }
  catch { return '' }
}
