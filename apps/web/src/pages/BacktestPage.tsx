import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Beaker, CheckCircle2, Clock3, GitCompareArrows, LoaderCircle, Play, RefreshCw, X } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { createBacktest, listBacktests } from '../features/backtests/api'
import { currentLanguage, type AppLanguage } from '../i18n'
import { formatDateTime, formatPercent } from '../lib/format'

export function BacktestPage() {
  const { t } = useTranslation()
  const language = currentLanguage()
  const [fastWindow, setFastWindow] = useState(20)
  const [slowWindow, setSlowWindow] = useState(60)
  const [days, setDays] = useState(365)
  const [formError, setFormError] = useState('')
  const [comparisonIds, setComparisonIds] = useState<string[]>([])
  const queryClient = useQueryClient()
  const runs = useQuery({ queryKey: ['backtests'], queryFn: listBacktests, refetchInterval: 5000 })
  const createRun = useMutation({
    mutationFn: createBacktest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['backtests'] }),
  })
  const comparisonRuns = (runs.data ?? []).filter((run) => comparisonIds.includes(run.id))

  function toggleComparison(runId: string) {
    setComparisonIds((current) => current.includes(runId)
      ? current.filter((id) => id !== runId)
      : [...current.slice(-2), runId])
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    setFormError('')
    if (fastWindow >= slowWindow) {
      setFormError(t('backtest.invalidWindows'))
      return
    }
    createRun.mutate({
      strategy_name: 'ma_cross_long_only',
      strategy_version: '1.0.0',
      exchange: 'binance',
      symbol: 'BTC/USDT',
      timeframe: '1d',
      days,
      parameters: { fast_window: fastWindow, slow_window: slowWindow },
      execution: {
        initial_capital: 1000,
        fee_rate: 0.001,
        slippage_rate: 0.0005,
        signal_on: 'candle_close',
        execute_on: 'next_candle_open',
      },
    })
  }

  return (
    <div className="animate-rise">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="eyebrow">{t('backtest.eyebrow')}</p><h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">{t('backtest.title')}</h1><p className="mt-3 text-sm text-muted">{t('backtest.description')}</p></div>
        <button className="button-outline w-fit" onClick={() => runs.refetch()} type="button"><RefreshCw size={16} />{t('backtest.refresh')}</button>
      </div>

      <section className="mt-8 grid gap-5 xl:grid-cols-[0.74fr_1.26fr]">
        <form className="research-card h-fit p-6 sm:p-7" onSubmit={submit}>
          <div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><Beaker size={19} /></span><div><p className="text-xs text-muted">{t('backtest.newExperiment')}</p><h2 className="font-bold">{t('backtest.strategyName')}</h2></div></div>
          <div className="mt-6 grid gap-5">
            <label className="grid gap-2 text-sm font-semibold">{t('backtest.symbol')}<input className="field-control text-muted" disabled value="BTC/USDT" /></label>
            <div className="grid grid-cols-2 gap-4">
              <label className="grid gap-2 text-sm font-semibold">{t('backtest.fastWindow')}<input className="field-control" min="2" onChange={(event) => setFastWindow(Number(event.target.value))} type="number" value={fastWindow} /></label>
              <label className="grid gap-2 text-sm font-semibold">{t('backtest.slowWindow')}<input className="field-control" min="3" onChange={(event) => setSlowWindow(Number(event.target.value))} type="number" value={slowWindow} /></label>
            </div>
            <label className="grid gap-2 text-sm font-semibold">{t('backtest.historyRange')}<select className="field-control" onChange={(event) => setDays(Number(event.target.value))} value={days}><option value={300}>{t('backtest.recentDays', { days: 300 })}</option><option value={365}>{t('backtest.recentDays', { days: 365 })}</option><option value={730}>{t('backtest.recentDays', { days: 730 })}</option></select></label>
            <div className="rounded-xl bg-[#f8f8fb] p-4 text-xs leading-6 text-muted"><p>{t('backtest.fee')}</p><p>{t('backtest.slippage')}</p><p>{t('backtest.execution')}</p></div>
          </div>
          {(formError || createRun.error) && <p className="mt-4 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700"><AlertCircle className="shrink-0" size={15} />{formError || t('backtest.createError')}</p>}
          <button className="button-primary mt-6 w-full" disabled={createRun.isPending} type="submit">{createRun.isPending ? <LoaderCircle className="animate-spin" size={17} /> : <Play size={17} />}{createRun.isPending ? t('backtest.creating') : t('backtest.run')}</button>
        </form>

        <div className="research-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-line px-5 py-5 sm:px-7"><div><h2 className="font-bold">{t('backtest.records')}</h2><p className="mt-1 text-xs text-muted">{t('backtest.recordsDescription')}</p></div><span className="text-xs text-muted">{t('backtest.recordCount', { count: runs.data?.length ?? 0 })}</span></div>
          <div className="divide-y divide-line">
            {runs.data?.map((run) => {
              const returnValue = run.summary?.strategy_total_return
              const drawdown = run.summary?.strategy_max_drawdown
              return (
                <article className={`grid gap-4 px-5 py-5 sm:grid-cols-[1.15fr_0.8fr_auto] sm:items-center sm:px-7 ${comparisonIds.includes(run.id) ? 'bg-[#faf8ff]' : ''}`} key={run.id}>
                  <div><div className="flex items-center gap-2"><strong className="text-sm">MA {String(run.parameters.fast_window)} / {String(run.parameters.slow_window)}</strong><StatusBadge status={run.status} /></div><p className="mt-1.5 text-xs text-muted">{run.exchange.toUpperCase()} · {run.symbol} · {run.timeframe} · {formatDateTime(run.created_at, language)}</p></div>
                  <div className="grid grid-cols-2 gap-4 text-sm"><span><small className="block text-xs text-muted">{t('backtest.totalReturn')}</small><strong className="mt-1 block">{returnValue === undefined ? '—' : formatPercent(returnValue, language)}</strong></span><span><small className="block text-xs text-muted">{t('backtest.maxDrawdown')}</small><strong className="mt-1 block">{drawdown === undefined ? '—' : formatPercent(drawdown, language)}</strong></span></div>
                  <div className="flex items-center justify-end gap-2"><code className="text-[11px] text-silver">{run.id.slice(0, 8)}</code>{run.status === 'succeeded' && <button aria-label={t('backtest.addComparison')} className={`grid size-8 place-items-center rounded-lg border ${comparisonIds.includes(run.id) ? 'border-brand bg-brand text-white' : 'border-line text-muted hover:border-brand hover:text-brand'}`} onClick={() => toggleComparison(run.id)} type="button"><GitCompareArrows size={14} /></button>}</div>
                  {run.error_message && <p className="text-xs text-red-700 sm:col-span-3">{run.error_message}</p>}
                </article>
              )
            })}
            {!runs.isPending && !runs.data?.length && <div className="grid min-h-64 place-items-center px-5 text-center"><div><Beaker className="mx-auto text-silver" size={30} /><p className="mt-4 text-sm font-semibold">{t('backtest.emptyTitle')}</p><p className="mt-2 text-xs text-muted">{t('backtest.emptyDescription')}</p></div></div>}
            {runs.isPending && <div className="grid min-h-64 place-items-center text-sm text-muted"><span className="flex items-center gap-2"><LoaderCircle className="animate-spin" size={17} />{t('backtest.loading')}</span></div>}
          </div>
        </div>
      </section>

      {comparisonRuns.length > 0 && <section className="research-card mt-5 overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-7"><div className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><GitCompareArrows size={17} /></span><div><h2 className="text-sm font-bold">{t('backtest.comparisonTitle')}</h2><p className="mt-0.5 text-xs text-muted">{t('backtest.comparisonHint')}</p></div></div><button className="grid size-8 place-items-center rounded-lg text-muted hover:bg-[#f1f1f4]" onClick={() => setComparisonIds([])} type="button"><X size={15} /></button></div>
        <div className="overflow-x-auto p-5 sm:p-7"><table className="w-full min-w-[720px] border-collapse text-left text-xs"><thead><tr className="border-b border-line text-muted"><th className="pb-3 font-medium">{t('backtest.metric')}</th>{comparisonRuns.map((run) => <th className="pb-3 font-medium" key={run.id}><span className="block text-ink">{run.strategy_name}</span><code>{run.id.slice(0, 8)}</code></th>)}</tr></thead><tbody><ComparisonRow label={t('backtest.totalReturn')} language={language} runs={comparisonRuns} summaryKey="strategy_total_return" /><ComparisonRow label={t('backtest.benchmarkReturn')} language={language} runs={comparisonRuns} summaryKey="benchmark_total_return" /><ComparisonRow label={t('backtest.maxDrawdown')} language={language} runs={comparisonRuns} summaryKey="strategy_max_drawdown" /><ComparisonRow label={t('backtest.tradeCount')} runs={comparisonRuns} summaryKey="trade_count" /><tr className="border-b border-line/70"><th className="py-3 font-medium text-muted">{t('backtest.configurationSource')}</th>{comparisonRuns.map((run) => <td className="py-3" key={run.id}>{run.strategy_config_version_id ? <code>{run.strategy_config_version_id.slice(0, 8)}</code> : t('backtest.temporaryParameters')}</td>)}</tr></tbody></table></div>
      </section>}
    </div>
  )
}

function ComparisonRow({ label, runs, summaryKey, language }: { label: string; runs: import('../types').BacktestRun[]; summaryKey: string; language?: AppLanguage }) {
  return <tr className="border-b border-line/70"><th className="py-3 font-medium text-muted">{label}</th>{runs.map((run) => { const value = run.summary?.[summaryKey]; return <td className="py-3 font-semibold" key={run.id}>{value === undefined ? '—' : language && summaryKey !== 'trade_count' ? formatPercent(value, language) : value}</td> })}</tr>
}

function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation()
  const succeeded = status === 'succeeded'
  const failed = status === 'failed'
  const Icon = succeeded ? CheckCircle2 : failed ? AlertCircle : Clock3
  return <span className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold ${succeeded ? 'bg-[#e8f7ef] text-success-dark' : failed ? 'bg-red-50 text-red-700' : 'bg-[#f0ecfe] text-brand-deep'}`}><Icon size={11} />{succeeded ? t('common.succeeded') : failed ? t('common.failed') : t('common.running')}</span>
}
