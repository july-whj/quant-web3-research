import { apiRequest } from '../../lib/api'
import type {
  BacktestRun,
  StrategyConfig,
  StrategyDefinition,
  StrategyPreview,
} from '../../types'

export interface StrategyPayload {
  strategy_name: string
  strategy_version?: string
  exchange: 'binance' | 'okx'
  symbol: 'BTC/USDT'
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w'
  days: number
  parameters: Record<string, number>
  risk: { max_position_pct: number }
  execution: {
    initial_capital: number
    fee_rate: number
    slippage_rate: number
    signal_on: 'candle_close'
    execute_on: 'next_candle_open'
  }
}

export function listStrategies() {
  return apiRequest<StrategyDefinition[]>('/strategies')
}

export function previewStrategy(
  strategyKey: string,
  payload: Omit<StrategyPayload, 'strategy_name' | 'days' | 'risk' | 'execution'> & {
    limit: number
  },
) {
  return apiRequest<StrategyPreview>(`/strategies/${strategyKey}/preview`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listStrategyConfigs() {
  return apiRequest<StrategyConfig[]>('/strategy-configs')
}

export function createStrategyConfig(name: string, payload: StrategyPayload) {
  return apiRequest<StrategyConfig>('/strategy-configs', {
    method: 'POST',
    body: JSON.stringify({ name, ...payload }),
  })
}

export function createStrategyConfigVersion(configId: string, payload: StrategyPayload) {
  return apiRequest<StrategyConfig>(`/strategy-configs/${configId}/versions`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function runStrategyConfig(configId: string, versionNumber?: number) {
  return apiRequest<BacktestRun>(`/strategy-configs/${configId}/backtests`, {
    method: 'POST',
    body: JSON.stringify({ version_number: versionNumber }),
  })
}
