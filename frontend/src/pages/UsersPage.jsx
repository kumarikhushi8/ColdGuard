import { useCallback, useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { useAuth } from '../context/AuthContext'

export default function UsersPage() {
  const { authFetch, user } = useAuth()
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', phone: '', role: 'operator', password: '' })
  const [msg, setMsg] = useState('')

  const fetcher = useCallback(async () => {
    const res = await authFetch('/api/users/')
    return res?.ok ? res.json() : []
  }, [authFetch])

  const { data: users, loading, refresh } = usePolling(fetcher, 30000)

  async function handleCreate(e) {
    e.preventDefault()
    setCreating(true); setMsg('')
    const res = await authFetch('/api/users/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    const data = await res.json()
    if (res.ok) {
      setMsg('User created ✓')
      setForm({ name: '', email: '', phone: '', role: 'operator', password: '' })
      refresh()
    } else {
      setMsg(data.detail ?? 'Error creating user')
    }
    setCreating(false)
  }

  async function toggleActive(userId, active) {
    await authFetch(`/api/users/${userId}/activate?active=${!active}`, { method: 'PATCH' })
    refresh()
  }

  const ROLE_COLORS = { admin: '#60a5fa', operator: '#4ade80', farmer: '#fbbf24' }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-semibold text-white">User Management</h1>
        <p className="text-sm text-gray-500 mt-0.5">Manage operators and farmers — admin only</p>
      </div>

      {/* Create user */}
      <div className="card p-5">
        <h2 className="text-sm font-medium text-gray-300 mb-4">Create New User</h2>
        <form onSubmit={handleCreate} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Name" value={form.name} onChange={v => setForm(f => ({...f, name: v}))} placeholder="Rajesh Patil" required />
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Role</label>
              <select value={form.role} onChange={e => setForm(f => ({...f, role: e.target.value}))}
                className="w-full px-3 py-2.5 rounded-xl text-sm text-white focus:outline-none"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                <option value="operator">Operator</option>
                <option value="farmer">Farmer</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {form.role !== 'farmer' ? (
              <Input label="Email" type="email" value={form.email} onChange={v => setForm(f => ({...f, email: v}))} placeholder="operator@farm.in" />
            ) : (
              <Input label="Phone" type="tel" value={form.phone} onChange={v => setForm(f => ({...f, phone: v}))} placeholder="9876543210" />
            )}
            {form.role !== 'farmer' && (
              <Input label="Password" type="password" value={form.password} onChange={v => setForm(f => ({...f, password: v}))} placeholder="Min 8 chars" />
            )}
          </div>
          {msg && (
            <div className={`text-xs px-3 py-2 rounded-lg ${msg.includes('✓') ? 'text-leaf-400 bg-leaf-400/10' : 'text-red-400 bg-red-400/10'}`}>
              {msg}
            </div>
          )}
          <button type="submit" disabled={creating}
            className="px-5 py-2.5 rounded-xl text-sm font-medium disabled:opacity-40 transition-colors"
            style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)' }}>
            {creating ? 'Creating...' : 'Create User'}
          </button>
        </form>
      </div>

      {/* User list */}
      <div className="card overflow-hidden">
        <div className="p-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <h2 className="text-sm font-medium text-gray-300">All Users ({(users ?? []).length})</h2>
        </div>
        {loading ? (
          <div className="p-8 text-center text-gray-500 text-sm">Loading...</div>
        ) : (
          <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            {(users ?? []).map(u => (
              <div key={u.id} className="flex items-center gap-4 px-4 py-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-medium"
                  style={{ background: `${ROLE_COLORS[u.role]}20`, color: ROLE_COLORS[u.role] }}>
                  {u.name[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-white font-medium">{u.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full"
                      style={{ background: `${ROLE_COLORS[u.role]}20`, color: ROLE_COLORS[u.role] }}>
                      {u.role}
                    </span>
                    {!u.active && <span className="text-xs text-red-400 bg-red-400/10 px-2 py-0.5 rounded-full">Inactive</span>}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {u.email || u.phone}
                    {u.last_login && <span className="ml-2 text-gray-600">Last: {new Date(u.last_login).toLocaleDateString()}</span>}
                  </div>
                </div>
                {u.id !== user?.id && (
                  <button onClick={() => toggleActive(u.id, u.active)}
                    className="text-xs px-3 py-1.5 rounded-lg transition-colors"
                    style={u.active
                      ? { background: 'rgba(248,113,113,0.1)', color: '#f87171' }
                      : { background: 'rgba(74,222,128,0.1)',  color: '#4ade80' }}>
                    {u.active ? 'Deactivate' : 'Activate'}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Input({ label, type = 'text', value, onChange, placeholder, required }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1.5">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder} required={required}
        className="w-full px-3 py-2.5 rounded-xl text-sm text-white placeholder-gray-600 focus:outline-none"
        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }} />
    </div>
  )
}
