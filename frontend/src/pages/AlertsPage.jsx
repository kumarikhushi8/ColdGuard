import { useCallback, useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'
import AlertItem from '../components/alerts/AlertItem'

export default function AlertsPage() {
  const [ackedIds, setAckedIds] = useState([])
  const [showAcked, setShowAcked] = useState(false)

  const activeFetcher = useCallback(() => api.alerts(),        [])
  const ackedFetcher  = useCallback(() => api.alerts(true),    [])

  const { data: active, loading: aLoading } = usePolling(activeFetcher, 8000)
  const { data: acked }                     = usePolling(ackedFetcher,  30000)

  const displayActive = (active ?? []).filter(a => !ackedIds.includes(a.id))

  function handleAck(id) {
    setAckedIds(ids => [...ids, id])
  }

  const criticalCount = displayActive.filter(a => a.severity === 'critical').length
  const warningCount  = displayActive.filter(a => a.severity === 'warning').length

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Alert Centre</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Real-time cold chain notifications with multilingual farmer alerts
          </p>
        </div>
      </div>

      {/* Summary pills */}
      <div className="flex gap-3 flex-wrap">
        <Pill label="Critical" count={criticalCount} color="#f87171" bg="rgba(248,113,113,0.12)" />
        <Pill label="Warning"  count={warningCount}  color="#fbbf24" bg="rgba(251,191,36,0.12)" />
        <Pill label="Total"    count={displayActive.length} color="#9ca3af" bg="rgba(255,255,255,0.06)" />
      </div>

      {/* Active alerts */}
      {aLoading ? (
        <div className="text-gray-500 text-sm text-center py-8">Loading alerts…</div>
      ) : displayActive.length === 0 ? (
        <div className="card p-10 text-center">
          <div className="text-3xl mb-3">✓</div>
          <div className="text-leaf-400 font-medium">All clear</div>
          <div className="text-gray-500 text-sm mt-1">No active alerts across all facilities</div>
        </div>
      ) : (
        <div className="space-y-2">
          {displayActive.map(a => (
            <AlertItem key={a.id} alert={a} onAck={handleAck} />
          ))}
        </div>
      )}

      {/* Acknowledged section */}
      <div>
        <button
          onClick={() => setShowAcked(s => !s)}
          className="text-sm text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-2"
        >
          <svg
            width="14" height="14" viewBox="0 0 14 14" fill="none"
            stroke="currentColor" strokeWidth="1.5"
            style={{ transform: showAcked ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}
          >
            <path d="M4 2l6 5-6 5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Show acknowledged ({(acked ?? []).length})
        </button>

        {showAcked && (
          <div className="mt-3 space-y-2 opacity-50">
            {(acked ?? []).map(a => (
              <AlertItem key={a.id} alert={a} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Pill({ label, count, color, bg }) {
  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
      style={{ background: bg, color, border: `1px solid ${color}30` }}
    >
      <span className="mono font-semibold">{count}</span>
      <span>{label}</span>
    </div>
  )
}
