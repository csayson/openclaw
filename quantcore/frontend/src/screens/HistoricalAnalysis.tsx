import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Cell, ScatterChart, Scatter, Legend,
} from 'recharts'
import { useTradingStore } from '@/store/tradingStore'
import { positionsApi } from '@/hooks/useApi'

const CHART_COLORS = {
  green: '#22c55e', red: '#ef4444', blue: '#3b82f6',
  purple: '#a855f7', orange: '#f97316', slate: '#64748b',
}

function SummaryCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="glass rounded-lg p-3">
      <div className="text-xs text-slate-500 mb-0.5">{label}</div>
      <div className="font-bold mono text-sm">{value}</div>
      {sub && <div className="text-xs text-slate-600 mt-0.5">{sub}</div>}
    </div>
  )
}

export default function HistoricalAnalysis() {
  const { selectedAccount } = useTradingStore()

  const { data: summary } = useQuery({
    queryKey: ['history-summary', selectedAccount?.id],
    queryFn: () => positionsApi.getSummary(selectedAccount!.id).then((r) => r.data),
    enabled: !!selectedAccount,
  })

  const { data: trades = [] } = useQuery({
    queryKey: ['closed-trades-all', selectedAccount?.id],
    queryFn: () => positionsApi.getClosed(selectedAccount!.id, { limit: 500 }).then((r) => r.data),
    enabled: !!selectedAccount,
  })

  // Build equity curve
  let cum = 0
  const equityCurve = trades.map((t: any) => {
    cum += t.pnl_usd || 0
    return { date: t.closed_at?.substring(0, 10), value: cum }
  })

  // P&L by day of week
  const dowMap: Record<string, number> = { Sun: 0, Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0 }
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  trades.forEach((t: any) => {
    if (t.closed_at) {
      const d = days[new Date(t.closed_at).getDay()]
      dowMap[d] = (dowMap[d] || 0) + (t.pnl_usd || 0)
    }
  })
  const dowData = days.map((d) => ({ day: d, pnl: dowMap[d] }))

  // P&L by strategy
  const stratMap: Record<string, number> = {}
  trades.forEach((t: any) => {
    stratMap[t.strategy_name] = (stratMap[t.strategy_name] || 0) + (t.pnl_usd || 0)
  })
  const stratData = Object.entries(stratMap).map(([name, pnl]) => ({ name, pnl }))

  // R-multiple distribution (simplified)
  const rMultiples = trades
    .filter((t: any) => t.entry_price && t.stop_loss && t.pnl_usd)
    .map((t: any) => {
      const riskPerUnit = Math.abs(t.entry_price - t.stop_loss)
      const r = t.pnl_usd / (riskPerUnit * t.lot_size)
      return { r: parseFloat(r.toFixed(2)), count: 1 }
    })

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <h1 className="text-xl font-bold">Historical Analysis</h1>

      {/* Summary header */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <SummaryCard label="Total Trades" value={String(summary.total_trades)} />
          <SummaryCard label="Win Rate" value={`${((summary.win_rate || 0) * 100).toFixed(1)}%`} />
          <SummaryCard label="Net P&L" value={`$${(summary.net_pnl || 0).toFixed(2)}`} />
          <SummaryCard label="Profit Factor" value={(summary.profit_factor || 0).toFixed(2)} />
          <SummaryCard label="Largest Win" value={`$${(summary.largest_win || 0).toFixed(2)}`} />
          <SummaryCard label="Largest Loss" value={`$${(summary.largest_loss || 0).toFixed(2)}`} />
        </div>
      )}

      {/* Chart 1: Equity Curve */}
      <div className="glass rounded-xl p-4">
        <h2 className="text-sm font-semibold mb-3">Equity Curve</h2>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={equityCurve}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
            <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', fontSize: 12 }} />
            <ReferenceLine y={0} stroke="#334155" />
            <Line type="monotone" dataKey="value" stroke={CHART_COLORS.green} dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Chart 4: P&L by Day of Week */}
        <div className="glass rounded-xl p-4">
          <h2 className="text-sm font-semibold mb-3">P&L by Day of Week</h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={dowData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', fontSize: 12 }} />
              <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
                {dowData.map((d, i) => (
                  <Cell key={i} fill={d.pnl >= 0 ? CHART_COLORS.green : CHART_COLORS.red} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 3: Win/Loss by Strategy */}
        <div className="glass rounded-xl p-4">
          <h2 className="text-sm font-semibold mb-3">P&L by Strategy</h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={stratData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 9, fill: '#64748b' }} width={120} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', fontSize: 12 }} />
              <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                {stratData.map((d, i) => (
                  <Cell key={i} fill={d.pnl >= 0 ? CHART_COLORS.green : CHART_COLORS.red} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 9: Trade Duration vs P&L */}
      {rMultiples.length > 0 && (
        <div className="glass rounded-xl p-4">
          <h2 className="text-sm font-semibold mb-3">R-Multiple Distribution</h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={rMultiples}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="r" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', fontSize: 12 }} />
              <ReferenceLine x={0} stroke="#334155" />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {rMultiples.map((d: any, i: number) => (
                  <Cell key={i} fill={d.r >= 0 ? CHART_COLORS.blue : CHART_COLORS.red} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {trades.length === 0 && (
        <div className="glass rounded-xl p-12 text-center text-slate-500">
          No historical trade data yet
        </div>
      )}
    </div>
  )
}
