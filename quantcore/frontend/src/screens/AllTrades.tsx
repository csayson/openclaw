import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Filter } from 'lucide-react'
import { format } from 'date-fns'
import { useTradingStore } from '@/store/tradingStore'
import { positionsApi } from '@/hooks/useApi'
import type { Trade } from '@/types'

type Tab = 'open' | 'closed'

function TradeRow({ trade }: { trade: Trade }) {
  const pnl = trade.pnl_usd ?? 0
  return (
    <tr className="border-t border-slate-800 hover:bg-surface-800/50 transition-colors">
      <td className="px-3 py-2 font-mono font-bold text-xs">{trade.instrument}</td>
      <td className="px-3 py-2">
        <span className={`text-xs px-1.5 py-0.5 rounded ${trade.direction === 'LONG' ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}`}>
          {trade.direction}
        </span>
      </td>
      <td className="px-3 py-2 text-xs text-slate-400">{trade.strategy_name}</td>
      <td className="px-3 py-2 text-xs mono">{trade.entry_price?.toFixed(5) || '—'}</td>
      <td className="px-3 py-2 text-xs mono text-slate-400">{trade.stop_loss?.toFixed(5) || '—'}</td>
      <td className="px-3 py-2 text-xs mono text-slate-400">{trade.take_profit?.toFixed(5) || '—'}</td>
      <td className="px-3 py-2 text-xs">{trade.lot_size}</td>
      <td className={`px-3 py-2 text-xs font-bold mono ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
        {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
      </td>
      <td className="px-3 py-2 text-xs text-slate-500">
        {trade.opened_at ? format(new Date(trade.opened_at), 'MMM d HH:mm') : '—'}
      </td>
      <td className="px-3 py-2">
        <span className={`text-xs px-1.5 py-0.5 rounded ${
          trade.status === 'OPEN' ? 'bg-blue-900/40 text-blue-400' :
          trade.status === 'CLOSED' ? 'bg-slate-700 text-slate-400' : 'text-slate-500'
        }`}>{trade.status}</span>
      </td>
    </tr>
  )
}

export default function AllTrades() {
  const { selectedAccount, isWindingDown, openPositions } = useTradingStore()
  const [tab, setTab] = useState<Tab>('open')

  const { data: closedTrades = [], isLoading } = useQuery<Trade[]>({
    queryKey: ['closed-trades', selectedAccount?.id],
    queryFn: () => positionsApi.getClosed(selectedAccount!.id).then((r) => r.data),
    enabled: !!selectedAccount && tab === 'closed',
  })

  const trades = tab === 'open' ? openPositions : closedTrades

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">All Trades</h1>
        <button className="flex items-center gap-2 border border-slate-700 rounded-lg px-3 py-1.5 text-xs hover:border-slate-500 transition-colors">
          <Download size={12} /> Export CSV
        </button>
      </div>

      {isWindingDown && (
        <div className="bg-orange-900/20 border border-orange-800 rounded-lg px-4 py-2 mb-4 text-xs text-orange-300">
          ⏹ SOFT STOP ACTIVE — No new trades. {openPositions.length} position(s) winding down.
          <div className="mt-1 w-full h-1 bg-surface-900 rounded-full">
            <div className="h-full bg-orange-500 rounded-full" style={{ width: `${((8 - openPositions.length) / 8) * 100}%` }} />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-slate-800 pb-2">
        {(['open', 'closed'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 text-sm rounded-lg transition-colors ${tab === t ? 'bg-brand-900/40 text-brand-400 border border-brand-800' : 'text-slate-500 hover:text-slate-300'}`}
          >
            {t === 'open' ? `Open (${openPositions.length})` : `Closed (${closedTrades.length})`}
          </button>
        ))}
      </div>

      <div className="glass rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="text-xs text-slate-500 border-b border-slate-800">
              {['Symbol', 'Dir', 'Strategy', 'Entry', 'SL', 'TP', 'Size', 'P&L ($)', 'Opened', 'Status'].map((h) => (
                <th key={h} className="px-3 py-2 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={10} className="px-3 py-8 text-center text-slate-500 text-sm">Loading…</td></tr>
            ) : trades.length === 0 ? (
              <tr><td colSpan={10} className="px-3 py-8 text-center text-slate-500 text-sm">No trades found</td></tr>
            ) : (
              trades.map((t) => <TradeRow key={t.id} trade={t} />)
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
