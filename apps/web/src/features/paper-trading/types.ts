export interface PaperBalance {
  asset: string
  available: string
  locked: string
}

export interface PaperPosition {
  symbol: string
  quantity: string
  average_cost: string
  mark_price: string
  market_value: string
  realized_pnl: string
  unrealized_pnl: string
}

export interface PaperAccount {
  id: string
  name: string
  exchange: 'binance' | 'okx'
  symbol: 'BTC/USDT'
  status: string
  fee_rate: string
  slippage_rate: string
  max_position_pct: string
  max_order_notional: string
  balances: PaperBalance[]
  position: PaperPosition
  equity: string
  total_fees: string
  total_gas: string
  created_at: string
}

export interface PaperOrder {
  id: string
  account_id: string
  bot_id: string | null
  client_order_id: string
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  status: string
  quantity: string
  limit_price: string | null
  filled_quantity: string
  average_price: string | null
  fee_amount: string
  slippage_amount: string
  gas_amount: string
  grid_level: number | null
  rejection_reason: string | null
  created_at: string
  filled_at: string | null
}

export interface PaperFill {
  id: string
  order_id: string
  side: 'buy' | 'sell'
  reference_price: string
  execution_price: string
  quantity: string
  quote_amount: string
  fee_amount: string
  slippage_amount: string
  gas_amount: string
  market_time: string
  created_at: string
}

export interface PaperLedgerEntry {
  id: string
  asset: string
  entry_type: string
  amount: string
  available_after: string
  locked_after: string
  reference_type: string | null
  reference_id: string | null
  description: string | null
  created_at: string
}

export interface PaperBot {
  id: string
  account_id: string
  name: string
  bot_type: string
  status: 'draft' | 'running' | 'paused' | 'stopped' | 'error'
  lower_price: string
  upper_price: string
  grid_count: number
  grid_mode: string
  investment: string
  parameters: { levels?: Array<{ index: number; price: string }> }
  realized_profit: string
  created_at: string
  started_at: string | null
  stopped_at: string | null
}

export interface PaperSnapshot {
  market_time: string
  equity: string
  quote_balance: string
  base_quantity: string
  mark_price: string
  realized_pnl: string
  unrealized_pnl: string
}
