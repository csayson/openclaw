import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Sidebar } from '@/components/ui/Sidebar'
import Login from '@/screens/Login'
import CreateAccount from '@/screens/CreateAccount'
import Dashboard from '@/screens/Dashboard'
import LivePositions from '@/screens/LivePositions'
import AllTrades from '@/screens/AllTrades'
import HistoricalAnalysis from '@/screens/HistoricalAnalysis'
import Reports from '@/screens/Reports'
import BrokerManager from '@/screens/BrokerManager'

function ProtectedLayout() {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<CreateAccount />} />

      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/positions" element={<LivePositions />} />
        <Route path="/trades" element={<AllTrades />} />
        <Route path="/analysis" element={<HistoricalAnalysis />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/brokers" element={<BrokerManager />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
