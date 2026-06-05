import { create } from 'zustand'
import type { TradingState, TradingAccount, Trade, KPIMetrics } from '@/types'

interface TradingStore {
  selectedAccount: TradingAccount | null
  tradingState: TradingState
  activeStrategies: string[]
  openPositions: Trade[]
  kpis: KPIMetrics
  isWindingDown: boolean

  setAccount: (account: TradingAccount) => void
  setState: (state: TradingState) => void
  setActiveStrategies: (strategies: string[]) => void
  setOpenPositions: (positions: Trade[]) => void
  updateKPIs: (kpis: Partial<KPIMetrics>) => void
  addPosition: (trade: Trade) => void
  removePosition: (tradeId: string) => void
  updatePosition: (tradeId: string, updates: Partial<Trade>) => void
}

export const useTradingStore = create<TradingStore>((set, get) => ({
  selectedAccount: null,
  tradingState: 'OFFLINE',
  activeStrategies: [],
  openPositions: [],
  kpis: { net_pnl_today: 0, win_rate_30d: 0, current_drawdown: 0, open_positions: 0 },
  isWindingDown: false,

  setAccount: (account) => set({ selectedAccount: account }),
  setState: (state) =>
    set({ tradingState: state, isWindingDown: state === 'WINDING_DOWN' }),
  setActiveStrategies: (strategies) => set({ activeStrategies: strategies }),
  setOpenPositions: (positions) =>
    set({ openPositions: positions, kpis: { ...get().kpis, open_positions: positions.length } }),
  updateKPIs: (kpis) => set((s) => ({ kpis: { ...s.kpis, ...kpis } })),
  addPosition: (trade) =>
    set((s) => ({ openPositions: [...s.openPositions, trade] })),
  removePosition: (tradeId) =>
    set((s) => ({ openPositions: s.openPositions.filter((p) => p.id !== tradeId) })),
  updatePosition: (tradeId, updates) =>
    set((s) => ({
      openPositions: s.openPositions.map((p) => (p.id === tradeId ? { ...p, ...updates } : p)),
    })),
}))
