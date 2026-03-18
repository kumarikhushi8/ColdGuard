import { useCallback, useState } from 'react'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'

const BASE = import.meta.env.VITE_API_URL || ''

async function notifFetch(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, opts)
  return res.json()
}

export default function NotificationsPage() {
  const statusFetcher = useCallback(() => notifFetch('/api/notifications/status'), [])
  const contactsFetcher = useCallback(() => notifFetch('/api/notifications/facilities'), [])

  const { data: status, loading: sLoading, refresh: refreshStatus } = usePolling(statusFetcher, 30000)
  const { data: contacts, loading: cLoading } = usePolling(contactsFetcher, 30000)

  const [testPhone, setTestPhone]     = useState('')
  const [testChannel, setTestChannel] = useState('whatsapp')
  const [testResult, setTestResult]   = useState(null)
  const [testing, setTesting]         = useState(false)

  const [manualFacility, setManualFacility] = useState('')
  const [manualMsg, setManualMsg]           = useState('')
  const [manualSev, setManualSev]           = useState('warning')
  const [manualResult, setManualResult]     = useState(null)
  const [sending, setSending]               = useState(false)

  async function handleTest() {
    if (!testPhone) return
    setTesting(true)
    setTestResult(null)
    const res = await notifFetch('/api/notifications/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: testPhone, channel: testChannel }),
    })
    setTestResult(res)
    setTesting(false)
  }

  async function handleManual() {
    if (!manualFacility || !manualMsg) return
    setSending(true)
    setManualResult(null)
    const res = await notifFetch('/api/notifications/send-alert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ facility_id: manualFacility, message: manualMsg, severity: manualSev }),
    })
    setManualResult(res)
    setSending(false)
  }

  async function updatePhone(facilityId, newPhone) {
    await notifFetch(`/api/notifications/facilities/${facilityId}/phone?phone=${encodeURIComponent(newPhone)}`, {
      method: 'PATCH',
    })
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-semibold text-white">Notifications</h1>
        <p className="text-sm text-gray-500 mt-0.5">WhatsApp + SMS alert configuration</p>
      </div>

      {/* Status cards */}
      {!sLoading && status && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard
            title="WhatsApp Business API"
            enabled={status.whatsapp?.enabled}
            configured={status.whatsapp?.configured}
            detail={status.whatsapp?.phone_id ? `ID: ${status.whatsapp.phone_id}` : 'Not configured'}
          />
          <StatusCard
            title="SMS (fast2sms)"
            enabled={status.sms?.enabled}
            configured={status.sms?.configured}
            detail={status.sms?.configured ? `Sender: ${status.sms.sender_id}` : 'Not configured'}
          />
          <div className="card p-4">
            <div className="text-xs text-gray-500 uppercase tracking-widest mb-2">Mode</div>
            <div className={`text-lg font-semibold mono ${status.mode === 'live' ? 'text-leaf-400' : 'text-warn-400'}`}>
              {status.mode === 'live' ? 'LIVE' : 'MOCK'}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {status.mode === 'live' ? 'Sending real messages' : 'Logging only — add credentials to go live'}
            </div>
          </div>
        </div>
      )}

      {/* Setup instructions */}
      {status?.mode === 'mock' && (
        <div className="card p-5 border-warn-600/30" style={{ borderColor: 'rgba(217,119,6,0.3)' }}>
          <div className="text-warn-400 font-medium text-sm mb-3">Setup Required — Currently in Mock Mode</div>
          <div className="space-y-4 text-sm text-gray-400">
            <SetupStep
              num="1"
              title="WhatsApp Business API (Meta)"
              steps={[
                'Go to developers.facebook.com → Create App → Business',
                'Add WhatsApp product → Get Started',
                'Copy your Phone Number ID and generate a token',
                'Add a test phone number in the portal',
                'Edit coldguard/.env.example → rename to .env → fill WHATSAPP_TOKEN + WHATSAPP_PHONE_ID',
                'Set WHATSAPP_ENABLED=true → restart: docker compose down && docker compose up',
              ]}
            />
            <SetupStep
              num="2"
              title="SMS via fast2sms.com (Free: 500 SMS/day)"
              steps={[
                'Sign up at fast2sms.com',
                'Dashboard → Dev API → copy your API key',
                'Add SMS_API_KEY to .env → SMS_ENABLED=true',
                'Restart Docker',
              ]}
            />
          </div>
        </div>
      )}

      {/* Test message sender */}
      <div className="card p-5">
        <h2 className="text-sm font-medium text-gray-300 mb-4">Send Test Message</h2>
        <div className="space-y-3">
          <div className="flex gap-3 flex-wrap">
            <input
              type="tel"
              placeholder="Phone: 9876543210"
              value={testPhone}
              onChange={e => setTestPhone(e.target.value)}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-white/20 min-w-[180px]"
            />
            <select
              value={testChannel}
              onChange={e => setTestChannel(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none"
            >
              <option value="whatsapp">WhatsApp</option>
              <option value="sms">SMS</option>
              <option value="both">Both</option>
            </select>
            <button
              onClick={handleTest}
              disabled={testing || !testPhone}
              className="px-5 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-40"
              style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)' }}
            >
              {testing ? 'Sending...' : 'Send Test'}
            </button>
          </div>
          {testResult && (
            <div className={`text-xs p-3 rounded-lg mono ${testResult.success ? 'text-leaf-400 bg-leaf-400/10' : 'text-danger-400 bg-danger-400/10'}`}>
              {JSON.stringify(testResult, null, 2)}
            </div>
          )}
        </div>
      </div>

      {/* Manual alert trigger */}
      <div className="card p-5">
        <h2 className="text-sm font-medium text-gray-300 mb-4">Trigger Manual Alert</h2>
        <div className="space-y-3">
          <div className="flex gap-3 flex-wrap">
            <select
              value={manualFacility}
              onChange={e => setManualFacility(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none min-w-[180px]"
            >
              <option value="">Select facility...</option>
              {(contacts ?? []).map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
            <select
              value={manualSev}
              onChange={e => setManualSev(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none"
            >
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Alert message..."
              value={manualMsg}
              onChange={e => setManualMsg(e.target.value)}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-white/20"
            />
            <button
              onClick={handleManual}
              disabled={sending || !manualFacility || !manualMsg}
              className="px-5 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-40"
              style={{ background: 'rgba(248,113,113,0.15)', color: '#f87171', border: '1px solid rgba(248,113,113,0.3)' }}
            >
              {sending ? 'Sending...' : 'Send Alert'}
            </button>
          </div>
          {manualResult && (
            <div className="text-xs p-3 rounded-lg mono text-gray-400 bg-white/5">
              {JSON.stringify(manualResult, null, 2)}
            </div>
          )}
        </div>
      </div>

      {/* Facility contacts */}
      {!cLoading && contacts?.length > 0 && (
        <div className="card p-5">
          <h2 className="text-sm font-medium text-gray-300 mb-4">Facility Contacts</h2>
          <div className="space-y-2">
            {contacts.map(f => (
              <FacilityContact key={f.id} facility={f} onUpdate={updatePhone} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatusCard({ title, enabled, configured, detail }) {
  const color = enabled && configured ? '#4ade80' : enabled ? '#fbbf24' : '#6b7280'
  const label = enabled && configured ? 'Active' : enabled ? 'Enabled (not configured)' : 'Disabled'
  return (
    <div className="card p-4">
      <div className="text-xs text-gray-500 uppercase tracking-widest mb-2">{title}</div>
      <div className="flex items-center gap-2 mb-1">
        <span className="w-2 h-2 rounded-full" style={{ background: color }} />
        <span className="text-sm font-medium" style={{ color }}>{label}</span>
      </div>
      <div className="text-xs text-gray-600">{detail}</div>
    </div>
  )
}

function SetupStep({ num, title, steps }) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors">
        <span className="w-5 h-5 rounded-full bg-white/10 text-xs flex items-center justify-center shrink-0">{num}</span>
        <span className="font-medium">{title}</span>
        <span className="text-gray-600 ml-1">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <ol className="mt-2 ml-7 space-y-1 text-xs text-gray-500 list-decimal">
          {steps.map((s, i) => <li key={i}>{s}</li>)}
        </ol>
      )}
    </div>
  )
}

function FacilityContact({ facility, onUpdate }) {
  const [editing, setEditing] = useState(false)
  const [phone, setPhone] = useState(facility.owner_phone)
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    await onUpdate(facility.id, phone)
    setSaving(false)
    setEditing(false)
  }

  return (
    <div className="flex items-center gap-4 p-3 rounded-xl bg-white/[0.03] border border-white/5">
      <div className="flex-1 min-w-0">
        <div className="text-sm text-white font-medium truncate">{facility.name}</div>
        <div className="text-xs text-gray-500">{facility.owner_name} · {facility.location}</div>
      </div>
      {editing ? (
        <div className="flex items-center gap-2">
          <input
            value={phone}
            onChange={e => setPhone(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white w-36 focus:outline-none"
          />
          <button onClick={save} disabled={saving} className="text-xs text-leaf-400 hover:text-white transition-colors">
            {saving ? '...' : 'Save'}
          </button>
          <button onClick={() => setEditing(false)} className="text-xs text-gray-600 hover:text-white transition-colors">
            Cancel
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <span className="mono text-xs text-gray-400">{facility.owner_phone}</span>
          <button onClick={() => setEditing(true)} className="text-xs text-gray-600 hover:text-white transition-colors">
            Edit
          </button>
        </div>
      )}
    </div>
  )
}
