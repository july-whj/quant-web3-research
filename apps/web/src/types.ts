export interface AuthChallenge {
  address: `0x${string}`
  chain_id: number
  message: string
  expires_at: string
}

export interface CurrentUser {
  id: string
  address: `0x${string}`
  chain_id: number
  created_at: string
  last_login_at: string
}

export interface StrategyDefinition {
  key: string
  version: string
  kind: 'signal' | 'schedule' | 'grid'
  title: string
  description: string
  default_warmup_bars: number
  data_requirements: {
    fields: string[]
    market_types: string[]
    timeframes: string[]
    closed_candles_only: boolean
  }
  parameters_schema: {
    properties?: Record<string, {
      type?: string
      title?: string
      description?: string
      default?: number
      minimum?: number
      maximum?: number
    }>
    required?: string[]
  }
  plots: StrategyPlotDefinition[]
}

export interface StrategyPlotDefinition {
  key: string
  label: string
  pane: 'price' | 'indicator'
  color: string
}

export interface StrategyPreview {
  strategy_name: string
  strategy_version: string
  explanation: string
  warmup_bars: number
  candles: import('./features/market-chart/types').MarketCandle[]
  plots: Array<StrategyPlotDefinition & {
    points: Array<{ time: string; value: string }>
  }>
  signals: Array<{
    signal_time: string
    execution_time: string
    side: 'buy' | 'sell'
    signal_price: string
    execution_price: string
    target_position: string
    position_delta: string
    reason: string
  }>
}

export interface StrategyConfigVersion {
  id: string
  config_id: string
  version_number: number
  strategy_name: string
  strategy_version: string
  exchange: string
  symbol: string
  timeframe: string
  days: number
  parameters: Record<string, number>
  risk_config: { max_position_pct: number }
  execution_config: {
    initial_capital: number
    fee_rate: number
    slippage_rate: number
    signal_on: 'candle_close'
    execute_on: 'next_candle_open'
  }
  created_at: string
}

export interface StrategyConfig {
  id: string
  name: string
  status: string
  latest_version_number: number
  created_at: string
  updated_at: string
  versions: StrategyConfigVersion[]
}

export interface BacktestRun {
  id: string
  strategy_name: string
  strategy_version: string
  strategy_config_version_id: string | null
  exchange: string
  symbol: string
  timeframe: string
  days: number
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'cancelled'
  parameters: Record<string, number | string>
  risk_config: Record<string, number> | null
  execution_config: Record<string, number | string> | null
  data_snapshot: Record<string, number | string | boolean> | null
  summary: Record<string, number> | null
  error_message: string | null
  created_at: string
  finished_at: string | null
}

export interface DatasetRecord {
  id: string
  exchange: string
  symbol: string
  timeframe: string
  row_count: number
  created_at: string
}

export interface MarketStreamRecord {
  exchange: string
  symbol: string
  timeframe: string
  status: 'starting' | 'connecting' | 'live' | 'degraded' | 'disconnected' | 'ready'
  row_count: number
  last_closed_open_time: string | null
  last_received_at: string | null
  last_persisted_at: string | null
  last_backfill_at: string | null
  reconnect_count: number
  backfilled_candles: number
  last_error: string | null
}
