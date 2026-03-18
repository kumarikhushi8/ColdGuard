import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

const BASE = import.meta.env.VITE_API_URL || ''

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('cg_user')
    const access = localStorage.getItem('cg_access')
    if (stored && access) {
      try { setUser(JSON.parse(stored)) } catch {}
    }
    setLoading(false)
  }, [])

  const login = useCallback((tokenData) => {
    localStorage.setItem('cg_access',  tokenData.access_token)
    localStorage.setItem('cg_refresh', tokenData.refresh_token)
    localStorage.setItem('cg_user',    JSON.stringify(tokenData.user))
    setUser(tokenData.user)
  }, [])

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('cg_refresh')
    if (refresh) {
      try {
        await fetch(`${BASE}/api/auth/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refresh }),
        })
      } catch {}
    }
    localStorage.removeItem('cg_access')
    localStorage.removeItem('cg_refresh')
    localStorage.removeItem('cg_user')
    setUser(null)
  }, [])

  const authFetch = useCallback(async (path, opts = {}) => {
    const access = localStorage.getItem('cg_access')
    const headers = {
      ...(opts.headers ?? {}),
      ...(access ? { Authorization: `Bearer ${access}` } : {}),
    }
    let res = await fetch(`${BASE}${path}`, { ...opts, headers })

    // Auto-refresh on 401
    if (res.status === 401) {
      const refresh = localStorage.getItem('cg_refresh')
      if (refresh) {
        const rr = await fetch(`${BASE}/api/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refresh }),
        })
        if (rr.ok) {
          const data = await rr.json()
          localStorage.setItem('cg_access',  data.access_token)
          localStorage.setItem('cg_refresh', data.refresh_token)
          headers.Authorization = `Bearer ${data.access_token}`
          res = await fetch(`${BASE}${path}`, { ...opts, headers })
        } else {
          logout()
          return null
        }
      }
    }
    return res
  }, [logout])

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, authFetch }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
