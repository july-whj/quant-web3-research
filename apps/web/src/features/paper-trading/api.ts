import { apiRequest } from '../../lib/api'
import type {
  PaperAccount,
  PaperBot,
  PaperFill,
  PaperLedgerEntry,
  PaperOrder,
  PaperSnapshot,
} from './types'

export function listPaperAccounts() {
  return apiRequest<PaperAccount[]>('/paper/accounts')
}

export function createPaperAccount(payload: {
  name: string
  exchange: 'binance' | 'okx'
  initial_funds: number
  fee_rate: number
  slippage_rate: number
  max_position_pct: number
  max_order_notional: number
}) {
  return apiRequest<PaperAccount>('/paper/accounts', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function depositPaperFunds(accountId: string, amount: number) {
  return apiRequest<PaperAccount>(`/paper/accounts/${accountId}/funds`, {
    method: 'POST',
    body: JSON.stringify({ amount, note: 'Web paper funds deposit' }),
  })
}

export function listPaperOrders(accountId: string) {
  return apiRequest<PaperOrder[]>(`/paper/accounts/${accountId}/orders`)
}

export function createPaperOrder(accountId: string, payload: {
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  quantity: number
  limit_price?: number
}) {
  return apiRequest<PaperOrder>(`/paper/accounts/${accountId}/orders`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function cancelPaperOrder(accountId: string, orderId: string) {
  return apiRequest<PaperOrder>(`/paper/accounts/${accountId}/orders/${orderId}`, {
    method: 'DELETE',
  })
}

export function listPaperFills(accountId: string) {
  return apiRequest<PaperFill[]>(`/paper/accounts/${accountId}/fills`)
}

export function listPaperLedger(accountId: string) {
  return apiRequest<PaperLedgerEntry[]>(`/paper/accounts/${accountId}/ledger`)
}

export function listPaperSnapshots(accountId: string) {
  return apiRequest<PaperSnapshot[]>(`/paper/accounts/${accountId}/snapshots`)
}

export function listPaperBots(accountId: string) {
  return apiRequest<PaperBot[]>(`/paper/accounts/${accountId}/bots`)
}

export function createPaperBot(accountId: string, payload: {
  name: string
  lower_price: number
  upper_price: number
  grid_count: number
  grid_mode: 'arithmetic' | 'geometric'
  investment: number
}) {
  return apiRequest<PaperBot>(`/paper/accounts/${accountId}/bots`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function controlPaperBot(
  accountId: string,
  botId: string,
  action: 'start' | 'pause' | 'stop',
) {
  return apiRequest<PaperBot>(`/paper/accounts/${accountId}/bots/${botId}/${action}`, {
    method: 'POST',
  })
}
