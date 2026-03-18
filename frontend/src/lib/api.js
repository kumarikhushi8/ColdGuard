const BASE = import.meta.env.VITE_API_URL || ''

async function apiFetch(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const api = {
  summary:       () => apiFetch('/api/dashboard/summary'),
  trend:         (id, hours = 24) => apiFetch(`/api/dashboard/facility/${id}/trend?hours=${hours}`),
  facilities:    () => apiFetch('/api/facilities/'),
  alerts:        () => apiFetch('/api/alerts/'),
  ackAlert:      (id) => fetch(`${BASE}/api/alerts/${id}/acknowledge`, { method: 'PATCH' }),
}
