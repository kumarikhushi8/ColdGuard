import { useCallback, useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { useAuth } from '../context/AuthContext'
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line, Legend
} from 'recharts'

const BASE = import.meta.env.VITE_API_URL || ''

function fmt_inr(n) {
  if (!n && n !== 0) return '—'
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`
  if (n >= 100000)   return `₹${(n / 100000).toFixed(2)}L`
  if (n >= 1000)     return `₹${(n / 1000).toFixed(1)}K`
  return `₹${Math.round(n)}`
}
function fmt_mt(n) {
  if (!n && n !== 0) return '—'
  return `${Number(n).toFixed(1)} MT`
}
function fmt_pct(n) {
  if (!n && n !== 0) return '—'
  return `${Number(n).toFixed(1)}%`
}

const PERIOD_OPTIONS = [
  { label: '7d',  days: 7  },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
]

const TT_STYLE = {
  background: '#111a14', border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 10, fontSize: 12, color: '#e8f0ea',
}

export default function AnalyticsPage() {
  const { authFetch } = useAuth()
  const [period, setPeriod] = useState(30)

  const summaryFetcher  = useCallback(async () => {
    const res = await authFetch(`/api/analytics/summary?days=${period}`)
    return res?.ok ? res.json() : null
  }, [authFetch, period])

  const timelineFetcher = useCallback(async () => {
    const res = await authFetch(`/api/analytics/risk-timeline?days=${Math.min(period, 30)}`)
    return res?.ok ? res.json() : []
  }, [authFetch, period])

  const { data, loading } = usePolling(summaryFetcher,  60000)
  const { data: timeline } = usePolling(timelineFetcher, 60000)

  async function downloadCSV() {
    const res = await authFetch(`/api/analytics/report/csv?days=${period}`)
    if (!res?.ok) return
    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url
    a.download = `coldguard_report_${new Date().toISOString().slice(0,10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Build chart data from facilities
  const barData = (data?.facilities ?? []).map(f => ({
    name:    f.facility_name.replace(' Cold', '').replace(' Hub', '').replace(' Store', ''),
    saved:   Math.round(f.loss_prevented_inr / 1000),
    cost:    Math.round(f.subscription_cost / 1000),
    roi:     f.roi_pct,
  }))

  // Timeline chart data
  const tlMap = {}
  ;(timeline ?? []).forEach(r => {
    const day = new Date(r.day).toLocaleDateString('en-IN', { day:'2-digit', month:'short' })
    if (!tlMap[day]) tlMap[day] = { day }
    tlMap[day][r.facility_name] = +(r.avg_risk * 100).toFixed(1)
  })
  const tlData = Object.values(tlMap)
  const facilityNames = [...new Set((timeline ?? []).map(r => r.facility_name))]
  const COLORS = ['#4ade80', '#60a5fa', '#fbbf24', '#f87171', '#a78bfa']

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Analytics</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Loss prevented · ROI · Excursions · ICAR-backed methodology
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Period selector */}
          <div className="flex p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.05)' }}>
            {PERIOD_OPTIONS.map(o => (
              <button key={o.days} onClick={() => setPeriod(o.days)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  period === o.days ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-white'
                }`}>
                {o.label}
              </button>
            ))}
          </div>
          {/* Download */}
          <button onClick={downloadCSV}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-colors"
            style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)' }}>
            <DownloadIcon /> Export CSV
          </button>
        </div>
      </div>

      {loading && !data ? <LoadingState /> : (
        <>
          {/* Hero KPI row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Loss Prevented"
              value={fmt_inr(data?.total_loss_prevented_inr)}
              sub={fmt_mt(data?.total_loss_prevented_mt) + ' saved'}
              color="#4ade80"
              icon="🌱"
            />
            <KpiCard
              label="System ROI"
              value={fmt_pct(data?.system_roi_pct)}
              sub={`vs ₹${(data?.total_subscription_cost/1000)?.toFixed(1)}K cost`}
              color="#60a5fa"
              icon="📈"
            />
            <KpiCard
              label="Excursions Caught"
              value={data?.total_excursions ?? '—'}
              sub={`${data?.total_alerts ?? 0} alerts fired`}
              color="#fbbf24"
              icon="🌡️"
            />
            <KpiCard
              label="Sensor Readings"
              value={(data?.total_readings ?? 0).toLocaleString('en-IN')}
              sub={`${data?.total_sensors ?? 0} active sensors`}
              color="#a78bfa"
              icon="📡"
            />
          </div>

          {/* Loss prevented vs cost bar chart */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-gray-300">Loss Prevented vs Subscription Cost (₹K)</h2>
              <span className="text-xs text-gray-600">Per facility · {period}-day period</span>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={barData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TT_STYLE} formatter={(v, n) => [`₹${v}K`, n === 'saved' ? 'Loss Prevented' : 'Subscription']} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
                <Bar dataKey="saved" name="Loss Prevented" fill="rgba(74,222,128,0.6)"  radius={[4,4,0,0]} />
                <Bar dataKey="cost"  name="Subscription"   fill="rgba(96,165,250,0.4)"  radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Risk timeline */}
          {tlData.length > 0 && (
            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-medium text-gray-300">Risk Score Timeline (%)</h2>
                <span className="text-xs text-gray-600">Daily average · all facilities</span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={tlData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={TT_STYLE} formatter={v => [`${v}%`, 'Risk']} />
                  <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
                  {facilityNames.map((name, i) => (
                    <Line key={name} type="monotone" dataKey={name}
                      stroke={COLORS[i % COLORS.length]} strokeWidth={2}
                      dot={false} connectNulls />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Per-facility breakdown */}
          <div className="card overflow-hidden">
            <div className="p-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
              <h2 className="text-sm font-medium text-gray-300">Facility Breakdown</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 uppercase tracking-widest border-b"
                    style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                    <Th>Facility</Th>
                    <Th>Crop</Th>
                    <Th>Capacity</Th>
                    <Th>Loss Prevented</Th>
                    <Th>Value Saved</Th>
                    <Th>ROI</Th>
                    <Th>Payback</Th>
                    <Th>Uptime</Th>
                    <Th>Excursions</Th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.facilities ?? []).map(f => (
                    <tr key={f.facility_id} className="border-b hover:bg-white/[0.02] transition-colors"
                      style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                      <td className="px-4 py-3">
                        <div className="text-white font-medium text-xs">{f.facility_name}</div>
                        <div className="text-gray-600 text-xs">{f.location}</div>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400 capitalize">{f.crop}</td>
                      <td className="px-4 py-3 mono text-xs text-gray-300">{f.capacity_mt} MT</td>
                      <td className="px-4 py-3 mono text-xs text-leaf-400">{fmt_mt(f.loss_prevented_mt)}</td>
                      <td className="px-4 py-3 mono text-xs text-leaf-400">{fmt_inr(f.loss_prevented_inr)}</td>
                      <td className="px-4 py-3">
                        <RoiBadge roi={f.roi_pct} />
                      </td>
                      <td className="px-4 py-3 mono text-xs text-gray-400">{f.payback_days}d</td>
                      <td className="px-4 py-3">
                        <UptimeBadge pct={f.uptime_pct} />
                      </td>
                      <td className="px-4 py-3 text-xs">
                        <span className="text-gray-300">{f.excursion_count}</span>
                        {f.critical_excursions > 0 && (
                          <span className="ml-1 text-red-400">({f.critical_excursions} critical)</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Methodology note */}
          <div className="card p-4 flex items-start gap-3">
            <span className="text-lg shrink-0">📚</span>
            <div className="text-xs text-gray-500 leading-relaxed">
              <span className="text-gray-400 font-medium">Methodology: </span>
              Loss prevented is calculated using ICAR's 2022 post-harvest loss study:
              16% baseline loss without monitoring → 4% with active cold chain monitoring = 12% prevented.
              Crop values based on Agmarknet 2023-24 modal prices.
              ROI = (Loss Prevented − Subscription Cost) / Subscription Cost × 100.
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function KpiCard({ label, value, sub, color, icon }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-2">
        <div className="text-xs text-gray-500 uppercase tracking-widest">{label}</div>
        <span style={{ fontSize: 18 }}>{icon}</span>
      </div>
      <div className="mono text-3xl font-semibold" style={{ color }}>{value}</div>
      <div className="text-xs text-gray-600 mt-1">{sub}</div>
    </div>
  )
}

function RoiBadge({ roi }) {
  const color = roi > 200 ? '#4ade80' : roi > 100 ? '#60a5fa' : roi > 0 ? '#fbbf24' : '#f87171'
  return (
    <span className="mono text-xs font-semibold" style={{ color }}>
      {roi > 0 ? '+' : ''}{roi?.toFixed(0)}%
    </span>
  )
}

function UptimeBadge({ pct }) {
  const color = pct >= 95 ? '#4ade80' : pct >= 80 ? '#fbbf24' : '#f87171'
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
      <span className="mono text-xs" style={{ color }}>{pct?.toFixed(1)}%</span>
    </div>
  )
}

function Th({ children }) {
  return <th className="px-4 py-2.5 text-left">{children}</th>
}

function DownloadIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M6.5 1v8M3 6l3.5 4L10 6" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M1 11h11" strokeLinecap="round"/>
    </svg>
  )
}

function LoadingState() {
  return (
    <div className="space-y-4">
      {[1,2,3].map(i => (
        <div key={i} className="card p-5 animate-pulse">
          <div className="h-3 bg-white/5 rounded w-1/4 mb-3" />
          <div className="h-8 bg-white/5 rounded w-1/3" />
        </div>
      ))}
    </div>
  )
}
