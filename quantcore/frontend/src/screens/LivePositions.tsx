import { AnimatePresence } from 'framer-motion'
import { Activity } from 'lucide-react'
import { useTradingStore } from '@/store/tradingStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { SmartChartCard } from '@/components/charts/SmartChartCard'

/**
 * Smart Chart Visibility Rules:
 *  - Chart SHOWN if instrument has ≥1 open position
 *  - Chart HIDDEN (5s delay) after last position on that instrument closes
 *  - Grid adapts: 1→full, 2→2-col, 3-4→2×2, 5+→scrollable list
 */
export default function LivePositions() {
  const { openPositions, isWindingDown, selectedAccount } = useTradingStore()
  useWebSocket(selectedAccount?.id)

  const gridClass =
    openPositions.length === 1
      ? 'grid-cols-1'
      : openPositions.length === 2
      ? 'grid-cols-2'
      : 'grid-cols-2'

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-brand-500" />
          <h1 className="text-xl font-bold">Live Positions</h1>
          <span className="bg-brand-900/50 text-brand-400 text-xs px-2 py-0.5 rounded-full border border-brand-800">
            {openPositions.length} open
          </span>
        </div>

        {isWindingDown && (
          <div className="bg-orange-900/30 border border-orange-700 text-orange-300 text-xs px-3 py-1.5 rounded-lg flex items-center gap-2">
            ⏹ WINDING DOWN — {openPositions.length} position(s) remaining
            {/* Wind-down progress */}
            <div className="w-24 h-1.5 bg-surface-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-orange-500 rounded-full transition-all"
                style={{ width: `${Math.min(100, (8 - openPositions.length) / 8 * 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Empty state */}
      {openPositions.length === 0 && (
        <div className="glass rounded-2xl p-16 text-center">
          <Activity className="mx-auto mb-4 text-slate-700" size={40} />
          <p className="text-slate-400 font-medium">No open positions</p>
          <p className="text-slate-600 text-sm mt-1">Charts appear automatically when trades are entered</p>
        </div>
      )}

      {/* Smart chart grid — only renders for instruments with open positions */}
      <AnimatePresence>
        <div className={`grid ${gridClass} gap-4`}>
          {openPositions.map((trade) => (
            <SmartChartCard
              key={trade.id}
              trade={trade}
              onClose={(id) => console.log('close', id)}
              onModify={(id) => console.log('modify', id)}
            />
          ))}
        </div>
      </AnimatePresence>
    </div>
  )
}
