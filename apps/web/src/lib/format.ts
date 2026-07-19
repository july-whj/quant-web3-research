export function shortenAddress(address: string, size = 5) {
  return `${address.slice(0, size + 2)}…${address.slice(-size)}`
}

import type { AppLanguage } from '../i18n'

export function formatPercent(value: number, language: AppLanguage = 'zh-CN') {
  return new Intl.NumberFormat(language, {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatDateTime(value: string, language: AppLanguage = 'zh-CN') {
  return new Intl.DateTimeFormat(language, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
