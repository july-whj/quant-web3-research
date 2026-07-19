import { apiRequest } from '../../lib/api'
import type { BacktestRun, StrategyDefinition } from '../../types'

export function listStrategies() {
  return apiRequest<StrategyDefinition[]>('/strategies')
}

export function listBacktests() {
  return apiRequest<BacktestRun[]>('/backtests')
}

export function createBacktest(payload: {
  strategy_name: string
  strategy_version?: string
  exchange: string
  symbol: string
  timeframe: string
  days: number
  parameters: Record<string, number>
  risk?: {
    max_position_pct: number
  }
  execution: {
    initial_capital: number
    fee_rate: number
    slippage_rate: number
    signal_on: 'candle_close'
    execute_on: 'next_candle_open'
  }
}) {
  return apiRequest<BacktestRun>('/backtests', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
