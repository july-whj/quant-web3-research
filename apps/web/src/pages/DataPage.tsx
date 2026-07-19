import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, Database, LoaderCircle, RefreshCw, Server, Waves } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { listDatasets, listMarketStreams } from '../features/datasets/api'
import { currentLanguage } from '../i18n'
import { formatDateTime } from '../lib/format'

export function DataPage() {
  const { t } = useTranslation()
  const language = currentLanguage()
  const datasets = useQuery({ queryKey: ['datasets'], queryFn: listDatasets })
  const streams = useQuery({
    queryKey: ['market-streams'],
    queryFn: listMarketStreams,
    refetchInterval: 10_000,
  })
  const sources = streams.data?.length
    ? streams.data.map((stream) => ({
        exchange: stream.exchange.toUpperCase(),
        symbol: stream.symbol,
        timeframe: stream.timeframe,
        records: String(stream.row_count),
        lastClosed: stream.last_closed_open_time,
        status: stream.status,
      }))
    : datasets.data?.length
    ? datasets.data.map((dataset) => ({
        exchange: dataset.exchange,
        symbol: dataset.symbol,
        timeframe: dataset.timeframe,
        records: String(dataset.row_count),
        lastClosed: null,
        status: 'ready',
      }))
    : [{ exchange: 'Binance', symbol: 'BTC/USDT', timeframe: '1d', records: '—', lastClosed: null, status: 'planned' }]
  const refreshing = datasets.isFetching || streams.isFetching

  function statusLabel(status: string) {
    if (status === 'live') return t('data.live')
    if (status === 'connecting') return t('data.connecting')
    if (status === 'degraded') return t('data.degraded')
    if (status === 'disconnected') return t('data.disconnected')
    if (status === 'starting') return t('data.starting')
    if (status === 'ready') return t('data.ready')
    return t('data.planned')
  }

  function statusStyle(status: string) {
    if (status === 'live' || status === 'ready') return 'bg-[#e8f7ef] text-success-dark'
    if (status === 'degraded' || status === 'disconnected') return 'bg-amber-50 text-amber-800'
    return 'bg-[#f2f2f5] text-muted'
  }

  return (
    <div className="animate-rise">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">{t('data.eyebrow')}</p>
          <h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">{t('data.title')}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{t('data.description')}</p>
        </div>
        <button
          className="button-primary w-fit"
          disabled={refreshing}
          onClick={() => void Promise.all([datasets.refetch(), streams.refetch()])}
          type="button"
        >
          {refreshing ? <LoaderCircle className="animate-spin" size={17} /> : <RefreshCw size={17} />}
          {t('data.refresh')}
        </button>
      </div>

      <section className="mt-8 research-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-7">
          <div><p className="font-bold">{t('data.datasets')}</p><p className="mt-1 text-xs text-muted">{t('data.storage')}</p></div>
          <span className="text-xs text-muted">{t('data.sourceCount', { count: sources.length })}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="bg-[#fafafd] text-xs text-muted">
              <tr><th className="px-7 py-3 font-medium">{t('data.exchange')}</th><th className="px-5 py-3 font-medium">{t('data.symbol')}</th><th className="px-5 py-3 font-medium">{t('data.timeframe')}</th><th className="px-5 py-3 font-medium">{t('data.records')}</th><th className="px-5 py-3 font-medium">{t('data.latestCandle')}</th><th className="px-7 py-3 text-right font-medium">{t('data.status')}</th></tr>
            </thead>
            <tbody className="divide-y divide-line">
              {sources.map((source) => (
                <tr key={`${source.exchange}-${source.timeframe}`}>
                  <td className="px-7 py-5 font-semibold">{source.exchange}</td><td className="px-5 py-5">{source.symbol}</td><td className="px-5 py-5 text-muted">{source.timeframe}</td><td className="px-5 py-5 text-muted">{source.records}</td><td className="px-5 py-5 text-muted">{source.lastClosed ? formatDateTime(source.lastClosed, language) : '—'}</td>
                  <td className="px-7 py-5 text-right"><span className={`inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-semibold ${statusStyle(source.status)}`}>{source.status === 'live' || source.status === 'ready' ? <CheckCircle2 size={13} /> : source.status === 'degraded' || source.status === 'disconnected' ? <AlertTriangle size={13} /> : <LoaderCircle size={13} />}{statusLabel(source.status)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-3">
        {[
          { icon: Server, title: t('data.exchangeApi'), text: t('data.exchangeApiText') },
          { icon: Database, title: t('data.hotStorage'), text: t('data.hotStorageText') },
          { icon: Waves, title: t('data.onchain'), text: t('data.onchainText') },
        ].map(({ icon: Icon, title, text }) => (
          <article className="research-card p-5" key={title}><Icon className="text-brand" size={22} /><h2 className="mt-5 font-bold">{title}</h2><p className="mt-2 text-sm leading-6 text-muted">{text}</p></article>
        ))}
      </section>
    </div>
  )
}
