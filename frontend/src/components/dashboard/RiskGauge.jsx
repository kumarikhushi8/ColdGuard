import { riskColor } from '../../lib/utils'

export default function RiskGauge({ score, level, size = 80 }) {
  const pct   = score ?? 0
  const color = riskColor(level)
  const r     = (size / 2) - 8
  const circ  = 2 * Math.PI * r
  const dash  = circ * pct
  const gap   = circ - dash

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6}
        />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none"
          stroke={color}
          strokeWidth={6}
          strokeDasharray={`${dash} ${gap}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s ease, stroke 0.4s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="mono font-medium text-sm" style={{ color }}>
          {Math.round(pct * 100)}%
        </span>
      </div>
    </div>
  )
}
