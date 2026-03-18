import { NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  const NAV = [
    { to: '/',              label: 'Dashboard',  icon: GridIcon,     roles: null },
    { to: '/alerts',        label: 'Alerts',     icon: BellIcon,     roles: null },
    { to: '/mandi',         label: 'Mandi',      icon: ChartIcon,    roles: null },
    { to: '/analytics',     label: 'Analytics',  icon: BarIcon,      roles: ['admin','operator'] },
    { to: '/notifications', label: 'Notify',     icon: MessageIcon,  roles: ['admin','operator'] },
    { to: '/users',         label: 'Users',      icon: UsersIcon,    roles: ['admin'] },
  ].filter(n => !n.roles || n.roles.includes(user?.role))

  async function handleLogout() { await logout(); navigate('/login') }

  return (
    <div className="flex min-h-screen">
      <aside className="flex flex-col shrink-0 transition-all duration-300"
        style={{ width: collapsed ? 64 : 220, background: '#0c1410', borderRight: '1px solid rgba(255,255,255,0.07)' }}>
        <div className="flex items-center gap-3 px-4 py-5 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <SnowflakeIcon />
          {!collapsed && <div><div className="font-semibold text-white text-sm leading-tight">ColdGuard</div><div className="text-xs" style={{ color: '#4ade80', letterSpacing: '0.08em' }}>LIVE</div></div>}
        </div>
        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-150 ${isActive ? 'bg-leaf-500/20 text-leaf-300 font-medium' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
              <Icon />{!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t space-y-2" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          {!collapsed && user && <div className="px-2 py-1"><div className="text-xs text-white font-medium truncate">{user.name}</div><div className="text-xs text-gray-600 capitalize">{user.role}</div></div>}
          <button onClick={handleLogout} className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors w-full"><LogoutIcon />{!collapsed && 'Sign out'}</button>
        </div>
        <button onClick={() => setCollapsed(c => !c)} className="m-2 p-2 rounded-lg text-gray-600 hover:text-white hover:bg-white/5 transition-colors self-end text-xs">{collapsed ? '→' : '←'}</button>
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}

const SnowflakeIcon = () => <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><circle cx="14" cy="14" r="14" fill="rgba(74,222,128,0.15)"/><text x="14" y="19" textAnchor="middle" fontSize="14" fill="#4ade80">❄</text></svg>
const GridIcon    = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="1" y="1" width="6" height="6" rx="1.5"/><rect x="9" y="1" width="6" height="6" rx="1.5"/><rect x="1" y="9" width="6" height="6" rx="1.5"/><rect x="9" y="9" width="6" height="6" rx="1.5"/></svg>
const BellIcon    = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M8 2a5 5 0 0 1 5 5v3l1 2H2l1-2V7a5 5 0 0 1 5-5Z"/><path d="M6.5 13a1.5 1.5 0 0 0 3 0"/></svg>
const ChartIcon   = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2 12l4-4 3 3 5-6"/><path d="M2 14h12"/></svg>
const BarIcon     = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="1" y="8" width="3" height="6" rx="1"/><rect x="6" y="4" width="3" height="10" rx="1"/><rect x="11" y="1" width="3" height="13" rx="1"/></svg>
const MessageIcon = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H2a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h3l3 3 3-3h3a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1Z"/></svg>
const UsersIcon   = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="6" cy="5" r="2.5"/><path d="M1 13c0-2.76 2.24-5 5-5s5 2.24 5 5"/><circle cx="12" cy="5" r="2"/><path d="M14 13c0-1.86-1.12-3.47-2.75-4.2"/></svg>
const LogoutIcon  = () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M5 12H2a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1h3"/><path d="M9 10l4-3-4-3"/><path d="M13 7H5"/></svg>
