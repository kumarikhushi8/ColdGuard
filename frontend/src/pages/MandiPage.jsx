import { useCallback, useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { useNavigate } from 'react-router-dom'

const BASE = import.meta.env.VITE_API_URL || ''
const apiFetch = (p) => fetch(`${BASE}${p}`).then(r => r.json())

const ACTION_CONFIG = {
  SELL_NOW:  { color: '#f87171', bg: 'rgba(248,113,113,0.12)', border: 'rgba(248,113,113,0.3)', label: 'SELL NOW',  emoji: '🔴' },
  SELL_SOON: { color: '#fbbf24', bg: 'rgba(251,191,36,0.12)',  border: 'rgba(251,191,36,0.3)',  label: 'SELL SOON', emoji: '🟡' },
  HOLD:      { color: '#4ade80', bg: 'rgba(74,222,128,0.12)',  border: 'rgba(74,222,128,0.3)',  label: 'HOLD',      emoji: '🟢' },
  MOVE_CROP: { color: '#f97316', bg: 'rgba(249,115,22,0.12)',  border: 'rgba(249,115,22,0.3)',  label: 'MOVE CROP', emoji: '🚨' },
}

const TREND_ICON = { rising: '↑', falling: '↓', stable: '→', unknown: '—' }
const TREND_COLOR = { rising: '#4ade80', falling: '#f87171', stable: '#9ca3af', unknown: '#6b7280' }

export default function MandiPage() {
  const navigate = useNavigate()
  const [lang, setLang] = useState('en')

  const advisoryFetcher  = useCallback(() => apiFetch('/api/mandi/advisory/all/summary'), [])
  const summaryFetcher   = useCallback(() => apiFetch('/api/mandi/prices/summary'), [])

  const { data: advisories, loading: aLoading } = usePolling(advisoryFetcher, 60000)
  const { data: prices,     loading: pLoading } = usePolling(summaryFetcher,  60000)

  const sellNow  = (advisories ?? []).filter(a => a.action === 'SELL_NOW').length
  const sellSoon = (advisories ?? []).filter(a => a.action === 'SELL_SOON').length
  const hold     = (advisories ?? []).filter(a => a.action === 'HOLD').length
  const move     = (advisories ?? []).filter(a => a.action === 'MOVE_CROP').length

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Mandi Advisory</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Live prices + spoilage risk → sell / hold / move decisions
          </p>
        </div>
        {/* Language toggle */}
        <div className="flex gap-1 p-1 rounded-xl bg-white/5">
          {['en','hi','mr'].map(l => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                lang === l ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-white'
              }`}
            >
              {l === 'en' ? 'English' : l === 'hi' ? 'हिंदी' : 'मराठी'}
            </button>
          ))}
        </div>
      </div>

      {/* Summary pills */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <SummaryPill label="Sell Now"  count={sellNow}  color="#f87171" />
        <SummaryPill label="Sell Soon" count={sellSoon} color="#fbbf24" />
        <SummaryPill label="Hold"      count={hold}     color="#4ade80" />
        <SummaryPill label="Move Crop" count={move}     color="#f97316" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Advisory cards */}
        <div className="xl:col-span-2 space-y-3">
          <SectionHead title="Facility Advisories" />
          {aLoading ? <Skeleton /> : (advisories ?? []).map(a => (
            <AdvisoryCard
              key={a.facility_id}
              advisory={a}
              lang={lang}
              onClick={() => navigate(`/facility/${a.facility_id}`)}
            />
          ))}
        </div>

        {/* Mandi price ticker */}
        <div className="space-y-3">
          <SectionHead title="Live Mandi Prices" />
          {pLoading ? <Skeleton /> : (
            <div className="card p-4 space-y-2">
              {(prices ?? []).map(p => (
                <PriceTicker key={p.crop} price={p} />
              ))}
              {(!prices || prices.length === 0) && (
                <div className="text-gray-600 text-sm text-center py-4">
                  Loading prices...
                </div>
              )}
            </div>
          )}

          {/* How it works */}
          <div className="card p-4 space-y-2">
            <div className="text-xs font-medium text-gray-400 uppercase tracking-widest mb-3">How it works</div>
            <HowStep icon="🌡️" text="Sensor reads temperature, humidity, ethylene" />
            <HowStep icon="🧠" text="ML model scores spoilage risk (0–100%)" />
            <HowStep icon="📊" text="Agmarknet fetches live mandi prices" />
            <HowStep icon="⚡" text="Advisory engine combines both signals" />
            <HowStep icon="📱" text="WhatsApp alert sent to farmer in Marathi" />
          </div>
        </div>
      </div>
    </div>
  )
}

function AdvisoryCard({ advisory: a, lang, onClick }) {
  const cfg = ACTION_CONFIG[a.action] ?? ACTION_CONFIG.HOLD
  const explanation = lang === 'hi' ? a.explanation_hi
                    : lang === 'mr' ? a.explanation_mr
                    : a.explanation_en

  const priceChange = a.current_price && a.price_7d_ago
    ? ((a.current_price - a.price_7d_ago) / a.price_7d_ago * 100).toFixed(1)
    : null

  return (
    <div
      className="card card-hover p-5 cursor-pointer"
      style={{ borderColor: cfg.border }}
      onClick={onClick}
    >
      <div className="flex items-start gap-4">
        <div className="shrink-0 flex flex-col items-center gap-1">
          <div
            className="px-3 py-1.5 rounded-xl text-xs font-semibold mono"
            style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}
          >
            {cfg.label}
          </div>
          <div className="text-xs text-gray-600 capitalize">{a.crop}</div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="font-medium text-white text-sm">{a.facility_name}</div>

          {explanation && (
            <p className="text-sm text-gray-400 mt-1.5 leading-snug">{explanation}</p>
          )}

          <div className="flex items-center gap-4 mt-3 flex-wrap">
            {a.current_price && (
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-gray-500">Price</span>
                <span className="mono text-xs text-white font-medium">
                  ₹{Math.round(a.current_price)}/qtl
                </span>
                {priceChange && (
                  <span
                    className="mono text-xs"
                    style={{ color: parseFloat(priceChange) >= 0 ? '#4ade80' : '#f87171' }}
                  >
                    {parseFloat(priceChange) >= 0 ? '+' : ''}{priceChange}%
                  </span>
                )}
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500">Trend</span>
              <span
                className="mono text-xs font-medium"
                style={{ color: TREND_COLOR[a.price_trend] ?? '#9ca3af' }}
              >
                {TREND_ICON[a.price_trend]} {a.price_trend}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500">Risk</span>
              <span className="mono text-xs text-white">{Math.round(a.risk_score * 100)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PriceTicker({ price: p }) {
  const trendColor = TREND_COLOR[p.trend] ?? '#9ca3af'
  const trendIcon  = TREND_ICON[p.trend]  ?? '—'
  const changePct  = p.change_pct ? parseFloat(p.change_pct) : null

  return (
    <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
      <div>
        <div className="text-sm text-white capitalize">{p.crop}</div>
      </div>
      <div className="text-right">
        <div className="mono text-sm text-white">₹{Math.round(p.current_price)}</div>
        <div className="flex items-center gap-1 justify-end">
          <span className="text-xs" style={{ color: trendColor }}>{trendIcon}</span>
          {changePct !== null && (
            <span className="mono text-xs" style={{ color: changePct >= 0 ? '#4ade80' : '#f87171' }}>
              {changePct >= 0 ? '+' : ''}{changePct}%
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function SummaryPill({ label, count, color }) {
  return (
    <div className="card p-4 flex flex-col gap-1">
      <div className="text-xs text-gray-500 uppercase tracking-widest">{label}</div>
      <div className="mono text-3xl font-semibold" style={{ color }}>{count}</div>
    </div>
  )
}

function HowStep({ icon, text }) {
  return (
    <div className="flex items-start gap-2.5 text-xs text-gray-500">
      <span style={{ fontSize: 14 }}>{icon}</span>
      <span>{text}</span>
    </div>
  )
}

function SectionHead({ title }) {
  return (
    <h2 className="text-xs font-medium text-gray-400 uppercase tracking-widest">{title}</h2>
  )
}

function Skeleton() {
  return (
    <div className="card p-5 space-y-3 animate-pulse">
      <div className="h-3 bg-white/5 rounded w-1/3" />
      <div className="h-3 bg-white/5 rounded w-2/3" />
      <div className="h-3 bg-white/5 rounded w-1/2" />
    </div>
  )
}
