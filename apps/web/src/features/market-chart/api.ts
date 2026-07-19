import { apiRequest } from '../../lib/api'
import type {
  MarketCandlePage,
  MarketChartPage,
  MarketExchange,
  MarketSignalPage,
  MarketTimeframe,
} from './types'

interface MarketPageRequest {
  exchange: MarketExchange
  timeframe: MarketTimeframe
  before?: string
  fastWindow: number
  slowWindow: number
  includeSignals: boolean
}

function marketParams(request: MarketPageRequest) {
  const params = new URLSearchParams({
    exchange: request.exchange,
    symbol: 'BTC/USDT',
    timeframe: request.timeframe,
    limit: '500',
  })
  if (request.before) params.set('before', request.before)
  return params
}

export async function getMarketChartPage(request: MarketPageRequest): Promise<MarketChartPage> {
  const params = marketParams(request)
  const candlePromise = apiRequest<MarketCandlePage>(`/market/candles?${params.toString()}`)

  if (!request.includeSignals) {
    return { candles: await candlePromise, signals: [] }
  }

  const signalParams = marketParams(request)
  signalParams.set('fast_window', String(request.fastWindow))
  signalParams.set('slow_window', String(request.slowWindow))
  const [candles, signalPage] = await Promise.all([
    candlePromise,
    apiRequest<MarketSignalPage>(`/market/signals?${signalParams.toString()}`),
  ])
  return { candles, signals: signalPage.items }
}
