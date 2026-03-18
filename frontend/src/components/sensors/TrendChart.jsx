import {
  ResponsiveContainer, ComposedChart, Line, Bar,
  XAxis, YAxis, Tooltip, Legend, CartesianGrid
} from 'recharts'
import { shortTime } from '../../lib/utils'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card p-3 text-xs space-y-1" style={{ minWidth: 140 }}>
      <div className="text-gray-400 mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.dataKey} className="flex justify-between gap-4">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="mono text-white">{Number(p.value).toFixed(2)}</span>
        </div>
      ))}
    </div>
  )
}

export default function TrendChart({ data, height = 220 }) {
  if (!data?.length) return (
    <div className="flex items-center justify-center text-gray-600 text-sm" style={{ height }}>
      No trend data yet
    </div>
  )

  const chartData = data.map(d => ({
    time:    shortTime(d.bucket),
    temp:    d.avg_temp   ? Number(d.avg_temp).toFixed(2)  : null,
    rh:      d.avg_rh     ? Number(d.avg_rh).toFixed(1)    : null,
    eth:     d.avg_eth    ? Number(d.avg_eth).toFixed(4)   : null,
    risk:    d.max_risk   ? Number(d.max_risk * 100).toFixed(1) : null,
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData} margin={{ top: 4, right: 12, left: -20, bottom: 0 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="time"
          tick={{ fill: '#6b7280', fontSize: 11 }}
          axisLine={false} tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          yAxisId="temp"
          tick={{ fill: '#6b7280', fontSize: 11 }}
          axisLine={false} tickLine={false}
          domain={['auto', 'auto']}
        />
        <YAxis
          yAxisId="risk"
          orientation="right"
          tick={{ fill: '#6b7280', fontSize: 11 }}
          axisLine={false} tickLine={false}
          domain={[0, 100]}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11, color: '#9ca3af', paddingTop: 8 }}
        />
        <Line
          yAxisId="temp" type="monotone" dataKey="temp"
          name="Temp °C" stroke="#60a5fa" strokeWidth={2}
          dot={false} connectNulls
        />
        <Line
          yAxisId="temp" type="monotone" dataKey="rh"
          name="RH %" stroke="#4ade80" strokeWidth={1.5}
          dot={false} connectNulls strokeDasharray="4 2"
        />
        <Bar
          yAxisId="risk" dataKey="risk"
          name="Risk %" fill="rgba(248,113,113,0.25)"
          radius={[2,2,0,0]}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
