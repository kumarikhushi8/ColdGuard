import { useParams, useNavigate } from 'react-router-dom'
import { useCallback, useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'
import TrendChart from '../components/sensors/TrendChart'
import RiskGauge from '../components/dashboard/RiskGauge'
import AlertItem from '../components/alerts/AlertItem'
import {
  formatTemp, formatRH, formatEth, formatScore,
  riskBadgeClass, riskColor, timeAgo
} from '../lib/utils'

const HOURS_OPTIONS = [6, 12, 24, 48]

export default function FacilityPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [hours, setHours] = useState(24)
  const [ackedIds, setAckedIds] = useState([])

  const summaryFetcher = useCallback(() => api.summary(), [])
  const trendFetcher   = useCallback(() => api.trend(id, hours), [id, hours])

  const { data: summary, loading: sLoading } = usePolling(summaryFetcher, 10000)
  const { data: trend,   loading: tLoading } = usePolling(trendFetcher,   15000)

  const facility = summary?.facilities?.find(f => f.id === id)
  const alerts   = (summary?.alerts ?? [])
    .filter(a => a.facility_id === id && !ackedIds.includes(a.id))

  if (sLoading) return <Spinner />

  if (!facility) return (
    <div className="p-6">
      <BackButton onClick={() => navigate('/')} />
      <div className="card p-8 mt-4 text-center text-gray-500 text-sm">Facility not found.</div>
    </div>
  )

  const color = riskColor(facility.risk_level)

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-start gap-4">
        <BackButton onClick={() => navigate('/')} />
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-semibold text-white">{facility.name}</h1>
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${riskBadgeClass(facility.risk_level)}`}>
              {(facility.risk_level ?? 'UNKNOWN').toUpperCase()}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {facility.location} · {facility.owner_name} · {facility.capacity_mt} MT capacity
          </p>
        </div>
      </div>

      {/* Top metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Temperature"  value={formatTemp(facility.temperature)}   color="#60a5fa" />
        <MetricCard label="Humidity"     value={formatRH(facility.humidity)}        color="#4ade80" />
        <MetricCard label="Ethylene"     value={formatEth(facility.ethylene_ppm)}   color="#fb923c" />
        <div className="card p-4 flex flex-col items-center justify-center gap-1">
          <RiskGauge score={facility.risk_score} level={facility.risk_level} size={72} />
          <span className="text-xs text-gray-500">Spoilage risk</span>
        </div>
      </div>

      {/* Trend chart */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-gray-300">Sensor Trend</h2>
          <div className="flex gap-1">
            {HOURS_OPTIONS.map(h => (
              <button
                key={h}
                onClick={() => setHours(h)}
                className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
                  hours === h
                    ? 'bg-white/10 text-white'
                    : 'text-gray-500 hover:text-white hover:bg-white/5'
                }`}
              >
                {h}h
              </button>
            ))}
          </div>
        </div>
        {tLoading
          ? <div className="flex items-center justify-center h-[220px] text-gray-600 text-sm">Loading…</div>
          : <TrendChart data={trend} height={220} />
        }
      </div>

      {/* Alerts for this facility */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-widest">
            Active Alerts ({alerts.length})
          </h2>
          {alerts.map(a => (
            <AlertItem
              key={a.id}
              alert={a}
              onAck={alertId => setAckedIds(ids => [...ids, alertId])}
            />
          ))}
        </div>
      )}

      {/* Last updated */}
      <p className="text-xs text-gray-700 pb-2">
        Last reading {timeAgo(facility.last_reading)}
      </p>
    </div>
  )
}

function MetricCard({ label, value, color }) {
  return (
    <div className="card p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="mono text-2xl font-medium" style={{ color }}>{value}</div>
    </div>
  )
}

function BackButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-white transition-colors shrink-0 mt-1"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 2L4 7l5 5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      Back
    </button>
  )
}

function Spinner() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-4xl blink">❄</div>
    </div>
  )
}
