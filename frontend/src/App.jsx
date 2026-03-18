import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import FacilityPage from './pages/FacilityPage'
import AlertsPage from './pages/AlertsPage'
import NotificationsPage from './pages/NotificationsPage'
import MandiPage from './pages/MandiPage'
import UsersPage from './pages/UsersPage'
import AnalyticsPage from './pages/AnalyticsPage'

function AuthCallback() {
  const { login } = useAuth()
  const navigate = useNavigate()
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const access_token  = params.get('access_token')
    const refresh_token = params.get('refresh_token')
    const role          = params.get('role')
    if (access_token) {
      login({ access_token, refresh_token, user: { role, name: 'Admin' } })
      navigate('/')
    } else { navigate('/login') }
  }, [])
  return <div className="min-h-screen flex items-center justify-center text-gray-400">Signing in...</div>
}

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login"         element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/*" element={
        <ProtectedRoute>
          <Layout>
            <Routes>
              <Route path="/"              element={<DashboardPage />} />
              <Route path="/facility/:id"  element={<FacilityPage />} />
              <Route path="/alerts"        element={<AlertsPage />} />
              <Route path="/mandi"         element={<MandiPage />} />
              <Route path="/analytics"     element={<AnalyticsPage />} />
              <Route path="/notifications" element={<NotificationsPage />} />
              <Route path="/users" element={
                <ProtectedRoute roles={['admin']}>
                  <UsersPage />
                </ProtectedRoute>
              } />
            </Routes>
          </Layout>
        </ProtectedRoute>
      } />
    </Routes>
  )
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
