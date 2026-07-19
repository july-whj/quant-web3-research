import { apiRequest } from '../../lib/api'
import type { DatasetRecord, MarketStreamRecord } from '../../types'

export function listDatasets() {
  return apiRequest<DatasetRecord[]>('/datasets')
}

export function listMarketStreams() {
  return apiRequest<MarketStreamRecord[]>('/market/streams')
}
