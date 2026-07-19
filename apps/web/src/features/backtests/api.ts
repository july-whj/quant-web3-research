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
  symbol: string
  timeframe: string
  days: number
  parameters: Record<string, number>
}) {
  return apiRequest<BacktestRun>('/backtests', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
