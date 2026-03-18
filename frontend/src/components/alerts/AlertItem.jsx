import { useState } from 'react'
import { severityBadgeClass, timeAgo } from '../../lib/utils'
import { api } from '../../lib/api'

export default function AlertItem({ alert, onAck }) {
  const [acking, setAcking]   = useState(false)
  const [expanded, setExpanded] = useState(false)

  async function handleAck(e) {
    e.stopPropagation()
    setAcking(true)
    await api.ackAlert(alert.id)
    onAck?.(alert.id)
  }

  return (
    <div
      className="card p-4 cursor-pointer hover:border-white/10 transition-all"
      onClick={() => setExpanded(x => !x)}
    >
      <div className="flex items-start gap-3">
        {/* Severity dot */}
        <div className="mt-1 shrink-0">
          <SeverityDot severity={alert.severity} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${severityBadgeClass(alert.severity)}`}>
              {alert.severity.toUpperCase()}
            </span>
            <span className="text-xs text-gray-500 truncate">{alert.facility_name}</span>
            <span className="text-xs text-gray-600 ml-auto shrink-0">{timeAgo(alert.created_at)}</span>
          </div>

          <p className="text-sm text-gray-200 mt-1.5 leading-snug">{alert.message}</p>

          {/* Marathi translation */}
          {expanded && alert.message_mr && alert.message_mr !== alert.message && (
            <div className="mt-2 p-2.5 rounded-lg bg-white/[0.03] border border-white/5">
              <div className="text-xs text-gray-600 mb-1">मराठी</div>
              <p className="text-sm text-gray-400">{alert.message_mr}</p>
            </div>
          )}

          {/* Hindi translation */}
          {expanded && alert.message_hi && alert.message_hi !== alert.message && (
            <div className="mt-2 p-2.5 rounded-lg bg-white/[0.03] border border-white/5">
              <div className="text-xs text-gray-600 mb-1">हिंदी</div>
              <p className="text-sm text-gray-400">{alert.message_hi}</p>
            </div>
          )}
        </div>

        <button
          onClick={handleAck}
          disabled={acking}
          className="shrink-0 text-xs px-3 py-1.5 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors disabled:opacity-40"
        >
          {acking ? '...' : 'Ack'}
        </button>
      </div>
    </div>
  )
}

function SeverityDot({ severity }) {
  const colors = { critical: '#f87171', warning: '#fbbf24', info: '#4ade80' }
  const color = colors[severity] ?? '#94a3b8'
  return (
    <div
      className={severity === 'critical' ? 'blink' : ''}
      style={{ width: 8, height: 8, borderRadius: '50%', background: color, marginTop: 2 }}
    />
  )
}
