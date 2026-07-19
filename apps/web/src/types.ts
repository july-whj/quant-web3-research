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
  name: string
  title: string
  description: string
  parameters: Array<{
    name: string
    label: string
    type: 'integer' | 'number'
    default: number
    minimum: number
  }>
}

export interface BacktestRun {
  id: string
  strategy_name: string
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'cancelled'
  parameters: Record<string, number | string>
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
