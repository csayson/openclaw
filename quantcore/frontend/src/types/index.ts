export type TradingState = 'OFFLINE' | 'CONNECTED' | 'ACTIVE' | 'PAUSED' | 'WINDING_DOWN' | 'EMERGENCY'
export type StopMode = 'SOFT' | 'HARD' | 'PAUSE'
export type TradeDirection = 'LONG' | 'SHORT'
export type TradeStatus = 'PENDING' | 'OPEN' | 'CLOSING' | 'CLOSED' | 'CANCELLED'
export type StrategyType = 'FUNDAMENTAL' | 'TECHNICAL'

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  totp_enabled: boolean
}

export interface TradingAccount {
  id: string
  account_type: 'DEMO' | 'LIVE'
  broker: string
  starting_capital: number
  current_equity: number
  trading_state: TradingState
  risk_tolerance: number
  max_daily_loss_pct: number
  max_open_positions: number
  enabled_markets: Record<string, boolean>
  kyc_status: string
}

export interface Trade {
  id: string
  instrument: string
  direction: TradeDirection
  strategy_name: string
  entry_price: number | null
  current_price?: number
  stop_loss: number | null
  take_profit: number | null
  lot_size: number
  pnl_usd: number | null
  pnl_pct: number | null
  status: TradeStatus
  opened_at: string | null
  closed_at: string | null
}

export interface TradingStatus {
  state: TradingState
  active_strategies: string[]
  open_positions: number
  started_at: string | null
  account_id: string
}

export interface KPIMetrics {
  net_pnl_today: number
  win_rate_30d: number
  current_drawdown: number
  open_positions: number
}

export interface Signal {
  signal_id: string
  timestamp: string
  instrument: string
  strategy: string
  strategy_type: StrategyType
  direction: TradeDirection
  entry_price: number
  stop_loss: number
  take_profit: number
  lot_size: number
  risk_amount_usd: number
  risk_reward_ratio: number
  confidence_score: number
  trading_state: TradingState
  new_entry_allowed: boolean
  regime: string
}

export interface BrokerConnection {
  id: string
  broker_name: string
  server_url: string | null
  is_demo: boolean
  is_connected: boolean
  last_connected_at: string | null
  latency_ms: number | null
}
