import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Activity, List, BarChart3, FileText, Wifi, TrendingUp, LogOut
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useTradingStore } from '@/store/tradingStore'
import { clsx } from 'clsx'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/positions', icon: Activity, label: 'Live Positions' },
  { to: '/trades', icon: List, label: 'All Trades' },
  { to: '/analysis', icon: BarChart3, label: 'Analysis' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/brokers', icon: Wifi, label: 'Brokers' },
]

const STATE_DOT: Record<string, string> = {
  ACTIVE: 'bg-green-400 animate-pulse',
  PAUSED: 'bg-yellow-400',
  WINDING_DOWN: 'bg-orange-400',
  OFFLINE: 'bg-slate-600',
  CONNECTED: 'bg-blue-400',
  EMERGENCY: 'bg-red-500',
}

export function Sidebar() {
  const { logout, user } = useAuthStore()
  const { tradingState } = useTradingStore()

  return (
    <aside className="w-56 min-h-screen bg-surface-900 border-r border-slate-800 flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-slate-800">
        <TrendingUp className="text-brand-500" size={18} />
        <span className="font-bold text-sm">QuantCore AI</span>
      </div>

      {/* State indicator */}
      <div className="px-4 py-2 border-b border-slate-800">
        <div className="flex items-center gap-2 text-xs">
          <span className={`w-2 h-2 rounded-full ${STATE_DOT[tradingState] || 'bg-slate-600'}`} />
          <span className="text-slate-400">{tradingState}</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-brand-900/40 text-brand-400 border border-brand-800/50'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800',
              )
            }
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="px-4 py-4 border-t border-slate-800">
        <div className="text-xs text-slate-500 mb-0.5">{user?.first_name} {user?.last_name}</div>
        <div className="text-xs text-slate-600 mb-2 truncate">{user?.email}</div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          <LogOut size={12} /> Sign out
        </button>
      </div>
    </aside>
  )
}
