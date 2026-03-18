export default function StatCard({ label, value, sub, accent, pulse }) {
  return (
    <div className="card p-5 flex flex-col gap-1">
      <div className="text-xs text-gray-500 uppercase tracking-widest">{label}</div>
      <div className="flex items-baseline gap-2">
        <span
          className={`text-4xl font-semibold mono ${pulse ? 'blink' : ''}`}
          style={{ color: accent ?? '#e8f0ea' }}
        >
          {value ?? '—'}
        </span>
      </div>
      {sub && <div className="text-xs text-gray-500">{sub}</div>}
    </div>
  )
}
