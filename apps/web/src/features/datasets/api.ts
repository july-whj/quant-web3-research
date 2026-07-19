import { apiRequest } from '../../lib/api'
import type { DatasetRecord } from '../../types'

export function listDatasets() {
  return apiRequest<DatasetRecord[]>('/datasets')
}
