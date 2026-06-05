import { useQuery } from '@tanstack/react-query'
import { Plus, Wifi, WifiOff, RefreshCw, Settings } from 'lucide-react'
import { useTradingStore } from '@/store/tradingStore'
import { accountsApi } from '@/hooks/useApi'
import type { BrokerConnection } from '@/types'

function StatusDot({ connected, demo }: { connected: boolean; demo: boolean }) {
  if (!connected) return <span className="inline-flex w-2.5 h-2.5 rounded-full bg-red-500" />
  return <span className={`inline-flex w-2.5 h-2.5 rounded-full ${demo ? 'bg-yellow-400' : 'bg-green-400'}`} />
}

function BrokerCard({ conn }: { conn: BrokerConnection }) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusDot connected={conn.is_connected} demo={conn.is_demo} />
          <span className="font-medium">{conn.broker_name}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded ${conn.is_demo ? 'bg-yellow-900/40 text-yellow-400' : 'bg-green-900/40 text-green-400'}`}>
            {conn.is_demo ? 'DEMO' : 'LIVE'}
          </span>
        </div>
        <div className="flex gap-1">
          <button className="p-1.5 rounded hover:bg-slate-700 transition-colors" title="Settings">
            <Settings size={14} />
          </button>
          <button className="p-1.5 rounded hover:bg-slate-700 transition-colors" title="Reconnect">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>
      <div className="text-xs text-slate-500 space-y-1">
        {conn.server_url && <div>Server: {conn.server_url}</div>}
        {conn.latency_ms != null && (
          <div className="flex items-center gap-1">
            <Wifi size={10} />
            Latency: <span className={conn.latency_ms < 50 ? 'text-green-400' : 'text-yellow-400'}>{conn.latency_ms.toFixed(0)}ms</span>
          </div>
        )}
        {conn.last_connected_at && (
          <div>Last connected: {new Date(conn.last_connected_at).toLocaleString()}</div>
        )}
      </div>
      {!conn.is_connected && (
        <button className="mt-3 w-full border border-brand-600 text-brand-400 hover:bg-brand-900/30 rounded-lg py-1.5 text-xs transition-colors">
          Reconnect
        </button>
      )}
    </div>
  )
}

export default function BrokerManager() {
  const { selectedAccount } = useTradingStore()
  const { data: brokers = [], isLoading } = useQuery<BrokerConnection[]>({
    queryKey: ['brokers', selectedAccount?.id],
    queryFn: () =>
      selectedAccount ? accountsApi.getBrokers(selectedAccount.id).then((r) => r.data) : [],
    enabled: !!selectedAccount,
  })

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold">Broker Connections</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {brokers.filter((b) => b.is_connected).length}/{brokers.length} connected
          </p>
        </div>
        <button className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 rounded-lg px-4 py-2 text-sm font-medium transition-colors">
          <Plus size={16} />
          Add Broker
        </button>
      </div>

      {isLoading ? (
        <div className="text-slate-400 text-sm">Loading connections…</div>
      ) : brokers.length === 0 ? (
        <div className="glass rounded-xl p-8 text-center">
          <WifiOff className="mx-auto mb-3 text-slate-600" size={32} />
          <p className="text-slate-400">No brokers connected yet</p>
          <button className="mt-3 bg-brand-600 hover:bg-brand-500 rounded-lg px-4 py-2 text-sm transition-colors">
            Connect your first broker
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {brokers.map((b) => <BrokerCard key={b.id} conn={b} />)}
        </div>
      )}

      {/* Auto-reconnect policy notice */}
      <div className="mt-6 text-xs text-slate-600 flex items-center gap-1">
        <RefreshCw size={10} />
        Auto-reconnect: exponential backoff 100ms → 30s max
      </div>
    </div>
  )
}
