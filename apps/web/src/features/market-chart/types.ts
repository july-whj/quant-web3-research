export type MarketExchange = 'binance' | 'okx'
export type MarketTimeframe = '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w'

export interface MarketCandle {
  open_time: string
  close_time: string
  open: string
  high: string
  low: string
  close: string
  volume: string
  trade_count: number | null
  source: string
}

export interface MarketCandlePage {
  exchange: MarketExchange
  symbol: 'BTC/USDT'
  timeframe: MarketTimeframe
  timezone: 'UTC'
  items: MarketCandle[]
  next_before: string | null
  has_more: boolean
}

export interface MarketSignal {
  signal_time: string
  execution_time: string
  side: 'buy' | 'sell'
  signal_price: string
  execution_price: string
  fast_ma: string
  slow_ma: string
  reason: 'ma_cross_up' | 'ma_cross_down'
}

export interface MarketSignalPage {
  exchange: MarketExchange
  symbol: 'BTC/USDT'
  timeframe: MarketTimeframe
  strategy_name: 'ma_cross_long_only'
  fast_window: number
  slow_window: number
  items: MarketSignal[]
}

export interface MarketChartPage {
  candles: MarketCandlePage
  signals: MarketSignal[]
}

export interface MarketChartSettings {
  volume: boolean
  fastMa: boolean
  slowMa: boolean
  macd: boolean
  signals: boolean
  executions: boolean
  fastWindow: number
  slowWindow: number
}
