import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const BASE = import.meta.env.VITE_API_URL || ''

export default function LoginPage() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const [tab, setTab]         = useState('email')   // email | otp
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [devOtp, setDevOtp]   = useState('')

  // Email form
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')

  // OTP form
  const [phone, setPhone]     = useState('')
  const [name, setName]       = useState('')
  const [otp, setOtp]         = useState('')

  async function handleEmailLogin(e) {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const res = await fetch(`${BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Login failed')
      login(data)
      navigate('/')
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function handleRequestOtp(e) {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const res = await fetch(`${BASE}/api/auth/otp/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, name: name || undefined }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Failed to send OTP')
      setOtpSent(true)
      if (data.dev_otp) setDevOtp(data.dev_otp)
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function handleVerifyOtp(e) {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const res = await fetch(`${BASE}/api/auth/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, otp }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Invalid OTP')
      login(data)
      navigate('/')
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'var(--bg-primary)' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>

        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3"
            style={{ background: 'rgba(74,222,128,0.15)', border: '1px solid rgba(74,222,128,0.3)' }}>
            <span style={{ fontSize: 28 }}>❄</span>
          </div>
          <h1 className="text-2xl font-semibold text-white">ColdGuard</h1>
          <p className="text-sm text-gray-500 mt-1">Cold chain intelligence for Indian agriculture</p>
        </div>

        {/* Tab switcher */}
        <div className="flex p-1 rounded-xl mb-6" style={{ background: 'rgba(255,255,255,0.05)' }}>
          <TabBtn label="Operator / Admin" active={tab === 'email'} onClick={() => { setTab('email'); setError('') }} />
          <TabBtn label="Farmer (OTP)"     active={tab === 'otp'}   onClick={() => { setTab('otp');   setError(''); setOtpSent(false) }} />
        </div>

        <div className="card p-6">

          {/* Email login */}
          {tab === 'email' && (
            <form onSubmit={handleEmailLogin} className="space-y-4">
              <Field label="Email" type="email" value={email} onChange={setEmail} placeholder="admin@coldguard.in" />
              <Field label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" />
              {error && <ErrorMsg msg={error} />}
              <SubmitBtn loading={loading} label="Sign in" />

              {/* Google OAuth */}
              <div className="relative flex items-center gap-3 py-1">
                <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.08)' }} />
                <span className="text-xs text-gray-600">or</span>
                <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.08)' }} />
              </div>
              <a href={`${BASE}/api/auth/google`}
                className="flex items-center justify-center gap-3 w-full py-2.5 rounded-xl text-sm text-gray-300 transition-colors hover:text-white"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                <GoogleIcon />
                Continue with Google (Admin)
              </a>

              <p className="text-xs text-gray-600 text-center mt-2">
                Default admin: admin@coldguard.in / Admin@123
              </p>
            </form>
          )}

          {/* OTP login */}
          {tab === 'otp' && !otpSent && (
            <form onSubmit={handleRequestOtp} className="space-y-4">
              <Field label="Mobile Number" type="tel" value={phone} onChange={setPhone} placeholder="9876543210" />
              <Field label="Your Name (first time only)" value={name} onChange={setName} placeholder="Rajesh Patil" />
              {error && <ErrorMsg msg={error} />}
              <SubmitBtn loading={loading} label="Send OTP" />
            </form>
          )}

          {tab === 'otp' && otpSent && (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div className="text-center text-sm text-gray-400 pb-1">
                OTP sent to <span className="text-white font-medium">{phone}</span>
              </div>
              {devOtp && (
                <div className="text-center p-3 rounded-xl text-sm mono"
                  style={{ background: 'rgba(74,222,128,0.1)', color: '#4ade80' }}>
                  Dev mode OTP: <strong>{devOtp}</strong>
                </div>
              )}
              <Field label="Enter OTP" value={otp} onChange={setOtp} placeholder="123456"
                maxLength={6} className="text-center text-2xl tracking-widest" />
              {error && <ErrorMsg msg={error} />}
              <SubmitBtn loading={loading} label="Verify OTP" />
              <button type="button" onClick={() => { setOtpSent(false); setDevOtp('') }}
                className="w-full text-xs text-gray-500 hover:text-white transition-colors py-1">
                ← Change number
              </button>
            </form>
          )}
        </div>

        {/* Role guide */}
        <div className="mt-4 grid grid-cols-3 gap-2">
          <RoleCard role="Admin" desc="Full access + Google" color="#60a5fa" />
          <RoleCard role="Operator" desc="Own facilities only" color="#4ade80" />
          <RoleCard role="Farmer" desc="Phone OTP login" color="#fbbf24" />
        </div>
      </div>
    </div>
  )
}

function TabBtn({ label, active, onClick }) {
  return (
    <button type="button" onClick={onClick}
      className="flex-1 py-2 rounded-lg text-xs font-medium transition-colors"
      style={active
        ? { background: 'rgba(255,255,255,0.1)', color: '#fff' }
        : { color: '#6b7280' }}>
      {label}
    </button>
  )
}

function Field({ label, type = 'text', value, onChange, placeholder, maxLength, className = '' }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        required
        className={`w-full px-4 py-2.5 rounded-xl text-sm text-white placeholder-gray-600 focus:outline-none focus:border-white/20 ${className}`}
        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
      />
    </div>
  )
}

function SubmitBtn({ loading, label }) {
  return (
    <button type="submit" disabled={loading}
      className="w-full py-3 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
      style={{ background: 'rgba(74,222,128,0.2)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)' }}>
      {loading ? 'Please wait...' : label}
    </button>
  )
}

function ErrorMsg({ msg }) {
  return (
    <div className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
      {msg}
    </div>
  )
}

function RoleCard({ role, desc, color }) {
  return (
    <div className="card p-3 text-center">
      <div className="text-xs font-medium mb-0.5" style={{ color }}>{role}</div>
      <div className="text-xs text-gray-600">{desc}</div>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16">
      <path fill="#4285F4" d="M15.5 8.17c0-.57-.05-1.12-.14-1.64H8v3.1h4.2a3.6 3.6 0 0 1-1.56 2.36v1.96h2.52C14.66 12.55 15.5 10.5 15.5 8.17z"/>
      <path fill="#34A853" d="M8 16c2.1 0 3.87-.7 5.16-1.88l-2.52-1.96c-.7.47-1.59.74-2.64.74-2.03 0-3.75-1.37-4.36-3.2H1.04v2.02A7.998 7.998 0 0 0 8 16z"/>
      <path fill="#FBBC05" d="M3.64 9.7A4.8 4.8 0 0 1 3.39 8c0-.59.1-1.16.25-1.7V4.28H1.04A8 8 0 0 0 0 8c0 1.29.31 2.51.86 3.58l2.05-1.59.73-.28z"/>
      <path fill="#EA4335" d="M8 3.18c1.14 0 2.17.39 2.97 1.16l2.23-2.23C11.86.79 10.1 0 8 0A7.998 7.998 0 0 0 1.04 4.28L3.64 6.3C4.25 4.47 5.97 3.18 8 3.18z"/>
    </svg>
  )
}
