import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePolling } from '../hooks/usePolling'
import StatCard from '../components/dashboard/StatCard'
import FacilityCard from '../components/dashboard/FacilityCard'
import AlertItem from '../components/alerts/AlertItem'

const BASE = import.meta.env.VITE_API_URL || ''

export default function DashboardPage() {
  const navigate = useNavigate()
  const [selectedState, setSelectedState] = useState('')
  const [search, setSearch] = useState('')

  const fetcher = useCallback(() => {
    const url = selectedState
      ? `${BASE}/api/dashboard/summary?state=${encodeURIComponent(selectedState)}`
      : `${BASE}/api/dashboard/summary`
    return fetch(url).then(r => r.json())
  }, [selectedState])

  const { data, loading, refresh } = usePolling(fetcher, 10000)

  const facilities = (data?.facilities ?? []).filter(f =>
    !search || f.name.toLowerCase().includes(search.toLowerCase()) ||
    f.location.toLowerCase().includes(search.toLowerCase())
  )

  const states = data?.states ?? []

  async function ackAlert(id) {
    await fetch(`${BASE}/api/alerts/${id}/acknowledge`, { method: 'PATCH' })
    refresh()
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Cold Chain Overview</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Live monitoring · {loading ? 'Refreshing...' : 'Updated less than a minute ago'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-leaf-400 animate-pulse" />
          <span className="text-xs text-leaf-400 font-medium mono">Live</span>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Facilities" value={data?.stats?.total_facilities ?? 0} />
        <StatCard label="Critical"    value={data?.stats?.critical_count  ?? 0} color="danger" />
        <StatCard label="High Risk"   value={data?.stats?.high_risk_count ?? 0} color="warn" />
        <StatCard label="Unacked Alerts" value={data?.stats?.unacked_alerts ?? 0} color="warn" />
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Search facility or city..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-4 py-2.5 rounded-xl text-sm text-white placeholder-gray-600 focus:outline-none"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
        />
        <select
          value={selectedState}
          onChange={e => setSelectedState(e.target.value)}
          className="px-4 py-2.5 rounded-xl text-sm text-white focus:outline-none min-w-[180px]"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          <option value="">All States ({data?.stats?.total_facilities ?? 0})</option>
          {states.map(s => (
            <option key={s.state} value={s.state}>
              {s.state} ({s.facility_count})
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Facilities */}
        <div className="xl:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-gray-400 uppercase tracking-widest">
              Facilities {selectedState && `· ${selectedState}`} ({facilities.length})
            </h2>
          </div>
          {loading && facilities.length === 0 ? (
            <div className="card p-8 text-center text-gray-500 text-sm">Loading facilities...</div>
          ) : facilities.length === 0 ? (
            <div className="card p-8 text-center text-gray-500 text-sm">No facilities found</div>
          ) : (
            facilities.map(f => (
              <FacilityCard
                key={f.id}
                facility={f}
                onClick={() => navigate(`/facility/${f.id}`)}
              />
            ))
          )}
        </div>

        {/* Alerts */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-gray-400 uppercase tracking-widest">Active Alerts</h2>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{
                background: (data?.alerts?.length ?? 0) > 0 ? 'rgba(248,113,113,0.15)' : 'rgba(255,255,255,0.05)',
                color:      (data?.alerts?.length ?? 0) > 0 ? '#f87171' : '#6b7280',
              }}>
              {data?.alerts?.length ?? 0}
            </span>
          </div>
          <div className="card p-3 space-y-2">
            {(data?.alerts ?? []).length === 0 ? (
              <div className="py-6 text-center text-sm text-leaf-500">All clear — no active alerts</div>
            ) : (
              (data?.alerts ?? []).map(a => (
                <AlertItem key={a.id} alert={a} onAck={ackAlert} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
