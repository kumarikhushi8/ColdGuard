import { useNavigate } from 'react-router-dom'
import RiskGauge from './RiskGauge'
import { riskBadgeClass, formatTemp, formatRH, formatEth, timeAgo } from '../../lib/utils'

export default function FacilityCard({ facility }) {
  const navigate = useNavigate()
  const f = facility

  return (
    <div
      className="card card-hover p-5 cursor-pointer animate-slide-up"
      onClick={() => navigate(`/facility/${f.id}`)}
    >
      <div className="flex items-start justify-between gap-4">
        {/* Left info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riskBadgeClass(f.risk_level)}`}>
              {(f.risk_level ?? 'unknown').toUpperCase()}
            </span>
          </div>
          <h3 className="font-medium text-white text-base truncate">{f.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5 truncate">{f.location}</p>

          {/* Sensor readings */}
          <div className="mt-3 grid grid-cols-3 gap-2">
            <Metric label="Temp"  value={formatTemp(f.temperature)} />
            <Metric label="RH"    value={formatRH(f.humidity)} />
            <Metric label="C₂H₄" value={formatEth(f.ethylene_ppm)} />
          </div>

          <p className="text-xs text-gray-600 mt-2">
            Updated {timeAgo(f.last_reading)}
          </p>
        </div>

        {/* Right gauge */}
        <div className="flex flex-col items-center gap-1 shrink-0">
          <RiskGauge score={f.risk_score} level={f.risk_level} size={76} />
          <span className="text-xs text-gray-500">Risk</span>
        </div>
      </div>

      {/* Capacity bar */}
      {f.capacity_mt && (
        <div className="mt-4 pt-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Capacity</span>
            <span className="mono">{f.capacity_mt} MT</span>
          </div>
        </div>
      )}
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="bg-white/[0.03] rounded-lg p-2">
      <div className="text-xs text-gray-600 mb-0.5">{label}</div>
      <div className="mono text-xs text-white font-medium">{value}</div>
    </div>
  )
}
