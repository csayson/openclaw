import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { createChart, IChartApi, ISeriesApi, LineStyle } from 'lightweight-charts'
import { TrendingUp, TrendingDown, X, Plus, ChevronDown } from 'lucide-react'
import { useTradingStore } from '@/store/tradingStore'
import type { Trade } from '@/types'

interface SmartChartCardProps {
  trade: Trade
  onClose?: (id: string) => void
  onModify?: (id: string) => void
}

export function SmartChartCard({ trade, onClose, onModify }: SmartChartCardProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartApi = useRef<IChartApi | null>(null)
  const candleApi = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const { isWindingDown } = useTradingStore()

  useEffect(() => {
    if (!chartRef.current) return

    const chart = createChart(chartRef.current, {
      layout: { background: { color: '#0f172a' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#1e293b' },
      timeScale: { borderColor: '#1e293b' },
      width: chartRef.current.clientWidth,
      height: 220,
    })
    chartApi.current = chart

    const candles = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })
    candleApi.current = candles

    // Entry line
    if (trade.entry_price) {
      const entryLine = chart.addLineSeries({
        color: '#60a5fa', lineWidth: 1, lineStyle: LineStyle.Solid, priceLineVisible: false,
      })
      entryLine.createPriceLine({ price: trade.entry_price, color: '#60a5fa', lineWidth: 1, lineStyle: LineStyle.Solid, title: 'Entry' })
    }

    // Stop loss
    if (trade.stop_loss) {
      const slSeries = chart.addLineSeries({ color: '#ef4444', lineStyle: LineStyle.Dashed, priceLineVisible: false })
      slSeries.createPriceLine({ price: trade.stop_loss, color: '#ef4444', lineWidth: 1, lineStyle: LineStyle.Dashed, title: 'SL' })
    }

    // Take profit
    if (trade.take_profit) {
      const tpSeries = chart.addLineSeries({ color: '#22c55e', lineStyle: LineStyle.Dashed, priceLineVisible: false })
      tpSeries.createPriceLine({ price: trade.take_profit, color: '#22c55e', lineWidth: 1, lineStyle: LineStyle.Dashed, title: 'TP' })
    }

    const handleResize = () => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth })
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [trade.id])

  const pnl = trade.pnl_usd ?? 0
  const pnlPositive = pnl >= 0
  const direction = trade.direction

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.4 } }}
      className="glass rounded-xl overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          {direction === 'LONG'
            ? <TrendingUp size={14} className="text-green-400" />
            : <TrendingDown size={14} className="text-red-400" />}
          <span className="font-bold mono">{trade.instrument}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${direction === 'LONG' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
            {direction}
          </span>
          <span className="text-xs text-slate-500">{trade.strategy_name}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`font-bold mono text-sm ${pnlPositive ? 'text-green-400' : 'text-red-400'}`}>
            {pnlPositive ? '+' : ''}{pnl.toFixed(2)} USD
          </span>
          <button onClick={() => onClose?.(trade.id)} className="text-slate-500 hover:text-slate-300">
            <ChevronDown size={16} />
          </button>
        </div>
      </div>

      {/* Winding down banner */}
      {isWindingDown && (
        <div className="bg-orange-900/30 border-b border-orange-800 px-4 py-1.5 text-xs text-orange-300">
          WINDING DOWN — No new trades being entered
        </div>
      )}

      {/* Chart */}
      <div ref={chartRef} className="w-full" />

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex items-center justify-between text-xs">
          <div className="flex gap-4 text-slate-400">
            <span>Size: <span className="text-white">{trade.lot_size}</span></span>
            <span>Entry: <span className="text-white mono">{trade.entry_price?.toFixed(5)}</span></span>
            <span>SL: <span className="text-red-400 mono">{trade.stop_loss?.toFixed(5)}</span></span>
            <span>TP: <span className="text-green-400 mono">{trade.take_profit?.toFixed(5)}</span></span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onModify?.(trade.id)}
              className="border border-slate-600 hover:border-slate-400 rounded px-2 py-1 text-xs transition-colors"
            >
              Modify SL/TP
            </button>
            {!isWindingDown && (
              <button className="border border-slate-600 hover:border-brand-500 rounded px-2 py-1 text-xs transition-colors">
                <Plus size={10} className="inline mr-1" />Add
              </button>
            )}
            <button
              onClick={() => onClose?.(trade.id)}
              className="border border-red-800 hover:bg-red-900/30 text-red-400 rounded px-2 py-1 text-xs transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
