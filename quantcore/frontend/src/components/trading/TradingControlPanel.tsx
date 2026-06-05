import { useState } from 'react'
import { Play, Pause, Square, AlertTriangle, Clock, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { useTradingStore } from '@/store/tradingStore'
import { tradingApi } from '@/hooks/useApi'
import type { TradingState, StopMode } from '@/types'

const STRATEGIES = [
  'MomentumBreakout', 'MacroTrendFollow', 'FundamentalValue',
  'EarningsSurprise', 'InsiderSignal', 'ThetaDecay',
  'MeanReversionPairs', 'DividendCapture', 'SentimentFlow', 'MacroCalendar',
]

const STATE_CONFIG: Record<TradingState, { label: string; color: string; dot: string }> = {
  OFFLINE: { label: 'OFFLINE', color: 'text-slate-400', dot: 'bg-slate-600' },
  CONNECTED: { label: 'CONNECTED', color: 'text-yellow-400', dot: 'bg-yellow-400' },
  ACTIVE: { label: 'ACTIVE', color: 'text-green-400', dot: 'bg-green-400' },
  PAUSED: { label: 'PAUSED', color: 'text-yellow-400', dot: 'bg-yellow-400' },
  WINDING_DOWN: { label: 'WINDING DOWN', color: 'text-orange-400', dot: 'bg-orange-400' },
  EMERGENCY: { label: 'EMERGENCY', color: 'text-red-500', dot: 'bg-red-500' },
}

function ConfirmStopModal({
  mode,
  onConfirm,
  onCancel,
  openCount,
}: {
  mode: StopMode
  onConfirm: () => void
  onCancel: () => void
  openCount: number
}) {
  const [confirmText, setConfirmText] = useState('')

  const modeInfo = {
    SOFT: {
      title: 'Soft Stop',
      description: [
        'Immediately blocks ALL new trade entries',
        'Cancels unfilled pending limit orders',
        `${openCount} open position(s) remain active`,
        'TP/SL and trailing stops stay managed',
        'System auto-idles when last position closes',
      ],
      buttonLabel: 'Confirm Soft Stop',
      buttonClass: 'bg-orange-600 hover:bg-orange-500',
      needsConfirmText: false,
    },
    PAUSE: {
      title: 'Pause Trading',
      description: [
        'Freezes signal scanning only',
        'All positions and orders remain active',
        'Resume with one click',
      ],
      buttonLabel: 'Pause',
      buttonClass: 'bg-yellow-600 hover:bg-yellow-500',
      needsConfirmText: false,
    },
    HARD: {
      title: 'Hard Stop',
      description: [
        '⚠️ Blocks new entries immediately',
        `Market-closes ALL ${openCount} open positions`,
        'Subject to slippage — use with caution',
      ],
      buttonLabel: 'Hard Stop — Close All',
      buttonClass: 'bg-red-700 hover:bg-red-600',
      needsConfirmText: false,
    },
  }

  const info = modeInfo[mode]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="glass rounded-2xl p-6 max-w-md w-full"
      >
        <h2 className="text-lg font-semibold mb-4">{info.title}</h2>
        <ul className="space-y-1.5 mb-5">
          {info.description.map((d, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
              <span className="text-brand-500 mt-0.5">•</span>
              {d}
            </li>
          ))}
        </ul>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 border border-slate-600 rounded-lg py-2 text-sm hover:border-slate-400 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${info.buttonClass}`}
          >
            {info.buttonLabel}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

function EmergencyModal({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) {
  const [text, setText] = useState('')
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
    >
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        className="glass border border-red-800 rounded-2xl p-6 max-w-md w-full"
      >
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="text-red-500" size={20} />
          <h2 className="text-lg font-bold text-red-400">EMERGENCY STOP</h2>
        </div>
        <ul className="space-y-1.5 mb-5 text-sm text-slate-300">
          {['Closes ALL positions at market immediately', 'Disconnects ALL broker connections', 'Sends SMS + email + push alert', 'Requires manual re-authentication to restart'].map((d, i) => (
            <li key={i} className="flex gap-2"><span className="text-red-500">•</span>{d}</li>
          ))}
        </ul>
        <div className="mb-4">
          <label className="text-xs text-slate-400 mb-1 block">Type "CONFIRM" to proceed:</label>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full bg-surface-900 border border-red-800 rounded-lg px-3 py-2 text-sm text-red-300 tracking-widest"
            placeholder="CONFIRM"
          />
        </div>
        <div className="flex gap-3">
          <button onClick={onCancel} className="flex-1 border border-slate-600 rounded-lg py-2 text-sm">Cancel</button>
          <button
            onClick={onConfirm}
            disabled={text !== 'CONFIRM'}
            className="flex-1 bg-red-700 hover:bg-red-600 disabled:opacity-40 rounded-lg py-2 text-sm font-bold transition-colors"
          >
            EXECUTE EMERGENCY STOP
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

export function TradingControlPanel() {
  const { tradingState, activeStrategies, openPositions, selectedAccount, setState } = useTradingStore()
  const [stopModal, setStopModal] = useState<StopMode | null>(null)
  const [showEmergency, setShowEmergency] = useState(false)
  const [startModal, setStartModal] = useState(false)
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(activeStrategies)

  const cfg = STATE_CONFIG[tradingState]

  const handleStart = async () => {
    if (!selectedAccount) return
    try {
      await tradingApi.start(selectedAccount.id, selectedStrategies)
      setState('ACTIVE')
      setStartModal(false)
      toast.success('Trading started')
    } catch {
      toast.error('Failed to start trading')
    }
  }

  const handleStop = async (mode: StopMode) => {
    if (!selectedAccount) return
    try {
      await tradingApi.stop(selectedAccount.id, mode)
      setState(mode === 'PAUSE' ? 'PAUSED' : 'WINDING_DOWN')
      setStopModal(null)
      toast.success(`${mode} stop executed`)
    } catch {
      toast.error('Failed to stop trading')
    }
  }

  const handleResume = async () => {
    if (!selectedAccount) return
    try {
      await tradingApi.resume(selectedAccount.id)
      setState('ACTIVE')
      toast.success('Trading resumed')
    } catch {
      toast.error('Failed to resume')
    }
  }

  const handleEmergency = async () => {
    if (!selectedAccount) return
    try {
      await tradingApi.emergency(selectedAccount.id)
      setState('OFFLINE')
      setShowEmergency(false)
      toast.error('Emergency stop executed')
    } catch {
      toast.error('Emergency stop failed')
    }
  }

  return (
    <>
      <div className="glass rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className={`inline-flex w-2.5 h-2.5 rounded-full ${cfg.dot} ${tradingState === 'ACTIVE' ? 'animate-pulse' : ''}`} />
            <span className={`font-bold mono text-sm ${cfg.color}`}>{cfg.label}</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1"><Activity size={12} /> {openPositions.length} positions</span>
            <span className="flex items-center gap-1"><Clock size={12} /></span>
          </div>
        </div>

        {/* Winding down banner */}
        <AnimatePresence>
          {tradingState === 'WINDING_DOWN' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="bg-orange-900/30 border border-orange-800 rounded-lg px-3 py-2 text-xs text-orange-300 mb-3"
            >
              ⏹ SOFT STOP ACTIVE — No new trades. {openPositions.length} position(s) winding down.
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex gap-2">
          {/* START */}
          {['OFFLINE', 'CONNECTED', 'IDLE'].includes(tradingState) && (
            <button
              onClick={() => setStartModal(true)}
              className="flex items-center gap-1.5 bg-green-700 hover:bg-green-600 rounded-lg px-3 py-2 text-xs font-medium transition-colors"
            >
              <Play size={12} /> START
            </button>
          )}

          {/* PAUSE */}
          {tradingState === 'ACTIVE' && (
            <button
              onClick={() => setStopModal('PAUSE')}
              className="flex items-center gap-1.5 bg-yellow-700 hover:bg-yellow-600 rounded-lg px-3 py-2 text-xs font-medium transition-colors"
            >
              <Pause size={12} /> PAUSE
            </button>
          )}

          {/* RESUME */}
          {tradingState === 'PAUSED' && (
            <button
              onClick={handleResume}
              className="flex items-center gap-1.5 bg-green-700 hover:bg-green-600 rounded-lg px-3 py-2 text-xs font-medium transition-colors"
            >
              <Play size={12} /> RESUME
            </button>
          )}

          {/* SOFT STOP */}
          {tradingState === 'ACTIVE' && (
            <button
              onClick={() => setStopModal('SOFT')}
              className="flex items-center gap-1.5 bg-orange-700 hover:bg-orange-600 rounded-lg px-3 py-2 text-xs font-medium transition-colors"
            >
              <Square size={12} /> SOFT STOP
            </button>
          )}

          {/* EMERGENCY */}
          <button
            onClick={() => setShowEmergency(true)}
            className="flex items-center gap-1.5 bg-red-900 hover:bg-red-800 border border-red-700 rounded-lg px-3 py-2 text-xs font-medium text-red-300 transition-colors ml-auto"
          >
            <AlertTriangle size={12} /> EMERGENCY
          </button>
        </div>
      </div>

      <AnimatePresence>
        {stopModal && (
          <ConfirmStopModal
            mode={stopModal}
            openCount={openPositions.length}
            onConfirm={() => handleStop(stopModal)}
            onCancel={() => setStopModal(null)}
          />
        )}
        {showEmergency && (
          <EmergencyModal onConfirm={handleEmergency} onCancel={() => setShowEmergency(false)} />
        )}
      </AnimatePresence>
    </>
  )
}
