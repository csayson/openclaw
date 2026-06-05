import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bell, Moon, Sun, TrendingUp, DollarSign, Percent, Activity, AlertTriangle } from 'lucide-react'
import { useTradingStore } from '@/store/tradingStore'
import { useAuthStore } from '@/store/authStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { accountsApi, tradingApi } from '@/hooks/useApi'
import { TradingControlPanel } from '@/components/trading/TradingControlPanel'

function KPICard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold mono ${color || 'text-white'}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  )
}

const STRATEGY_NAMES = [
  'MomentumBreakout', 'MacroTrendFollow', 'FundamentalValue',
  'EarningsSurprise', 'InsiderSignal', 'ThetaDecay',
  'MeanReversionPairs', 'DividendCapture', 'SentimentFlow', 'MacroCalendar',
]

export default function Dashboard() {
  const { user } = useAuthStore()
  const { selectedAccount, setAccount, tradingState, activeStrategies, kpis, openPositions } = useTradingStore()

  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list().then((r) => r.data),
  })

  useEffect(() => {
    if (accounts.length > 0 && !selectedAccount) {
      setAccount(accounts[0])
    }
  }, [accounts])

  const { data: status } = useQuery({
    queryKey: ['trading-status', selectedAccount?.id],
    queryFn: () => tradingApi.status(selectedAccount!.id).then((r) => r.data),
    enabled: !!selectedAccount,
    refetchInterval: 5000,
  })

  useWebSocket(selectedAccount?.id)

  return (
    <div className="min-h-screen bg-surface-950">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="text-brand-500" size={22} />
          <span className="font-bold text-lg">QuantCore AI</span>

          {/* Account selector */}
          <select
            value={selectedAccount?.id || ''}
            onChange={(e) => {
              const acc = accounts.find((a: any) => a.id === e.target.value)
              if (acc) setAccount(acc)
            }}
            className="bg-surface-900 border border-slate-700 rounded-lg px-2 py-1 text-xs ml-4"
          >
            {accounts.map((a: any) => (
              <option key={a.id} value={a.id}>
                {a.broker} ({a.account_type})
              </option>
            ))}
          </select>

          {selectedAccount && (
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${selectedAccount.account_type === 'LIVE' ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-yellow-900/50 text-yellow-400 border border-yellow-800'}`}>
              {selectedAccount.account_type}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button className="p-2 rounded-lg hover:bg-slate-800 transition-colors relative">
            <Bell size={16} />
          </button>
          <div className="w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center text-xs font-bold">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
        </div>
      </header>

      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Trading Engine Control */}
        <TradingControlPanel />

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            label="Net P&L Today"
            value={`${kpis.net_pnl_today >= 0 ? '+' : ''}$${kpis.net_pnl_today.toFixed(2)}`}
            color={kpis.net_pnl_today >= 0 ? 'text-green-400' : 'text-red-400'}
          />
          <KPICard
            label="Win Rate (30d)"
            value={`${(kpis.win_rate_30d * 100).toFixed(1)}%`}
            color="text-blue-400"
          />
          <KPICard
            label="Current Drawdown"
            value={`${(kpis.current_drawdown * 100).toFixed(2)}%`}
            color={kpis.current_drawdown > 0.03 ? 'text-red-400' : 'text-slate-200'}
          />
          <KPICard
            label="Open Positions"
            value={String(openPositions.length)}
            sub={`Max: ${selectedAccount?.max_open_positions || 8}`}
          />
        </div>

        {/* Strategy Status Bar */}
        <div className="glass rounded-xl p-4">
          <div className="text-xs text-slate-400 mb-3">Strategy Status</div>
          <div className="flex flex-wrap gap-2">
            {STRATEGY_NAMES.map((name) => {
              const isActive = activeStrategies.includes(name)
              return (
                <span
                  key={name}
                  className={`text-xs px-2 py-1 rounded-full border ${
                    isActive
                      ? 'bg-green-900/30 border-green-800 text-green-400'
                      : 'bg-slate-900/50 border-slate-700 text-slate-500'
                  }`}
                >
                  {isActive ? '✓' : '—'} {name}
                </span>
              )
            })}
          </div>
        </div>

        {/* Quick account info */}
        {selectedAccount && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="glass rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-1">Equity</div>
              <div className="font-bold mono">${selectedAccount.current_equity.toLocaleString()}</div>
            </div>
            <div className="glass rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-1">Broker</div>
              <div className="font-bold">{selectedAccount.broker}</div>
            </div>
            <div className="glass rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-1">Max Daily Loss</div>
              <div className="font-bold text-red-400">{selectedAccount.max_daily_loss_pct}%</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
