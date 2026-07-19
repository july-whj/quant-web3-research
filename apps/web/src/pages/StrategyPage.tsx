import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity,
  AlertCircle,
  BarChart3,
  Boxes,
  ChevronRight,
  FlaskConical,
  GitBranch,
  Layers3,
  LoaderCircle,
  Play,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TimerReset,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { createBacktest } from '../features/backtests/api'
import { MarketChart } from '../features/market-chart/MarketChart'
import type { MarketChartSettings } from '../features/market-chart/types'
import {
  createStrategyConfig,
  createStrategyConfigVersion,
  listStrategies,
  listStrategyConfigs,
  previewStrategy,
  runStrategyConfig,
  type StrategyPayload,
} from '../features/strategies/api'
import { currentLanguage, type AppLanguage } from '../i18n'
import { formatDateTime } from '../lib/format'
import type { StrategyConfig, StrategyConfigVersion, StrategyDefinition } from '../types'

const STRATEGY_ICONS = {
  ma_cross_long_only: Activity,
  rsi_reversal_long_only: TimerReset,
  staged_dca_long_only: Layers3,
  adaptive_spot_grid: Boxes,
}

const STRATEGY_I18N = {
  ma_cross_long_only: 'maCross',
  rsi_reversal_long_only: 'rsiReversal',
  staged_dca_long_only: 'stagedDca',
  adaptive_spot_grid: 'adaptiveGrid',
} as const

function defaultParameters(definition: StrategyDefinition) {
  return Object.fromEntries(
    Object.entries(definition.parameters_schema.properties ?? {}).map(([key, schema]) => [
      key,
      Number(schema.default ?? schema.minimum ?? 0),
    ]),
  )
}

function useDebouncedValue<T>(value: T, delay: number) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timeout = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(timeout)
  }, [delay, value])
  return debounced
}

export function StrategyPage() {
  const { t } = useTranslation()
  const language = currentLanguage()
  const queryClient = useQueryClient()
  const definitions = useQuery({ queryKey: ['strategies'], queryFn: listStrategies })
  const configs = useQuery({ queryKey: ['strategy-configs'], queryFn: listStrategyConfigs })
  const [strategyKey, setStrategyKey] = useState('ma_cross_long_only')
  const [parameters, setParameters] = useState<Record<string, number>>({})
  const [configName, setConfigName] = useState('BTC research #1')
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null)
  const [exchange, setExchange] = useState<'binance' | 'okx'>('binance')
  const [timeframe, setTimeframe] = useState<StrategyPayload['timeframe']>('1d')
  const [days, setDays] = useState(300)
  const [initialCapital, setInitialCapital] = useState(1000)
  const [feeRate, setFeeRate] = useState(0.001)
  const [slippageRate, setSlippageRate] = useState(0.0005)
  const [maxPositionPct, setMaxPositionPct] = useState(1)
  const [notice, setNotice] = useState('')

  const definition = definitions.data?.find((item) => item.key === strategyKey)
  const resolvedParameters = useMemo(
    () => Object.keys(parameters).length > 0
      ? parameters
      : definition ? defaultParameters(definition) : {},
    [definition, parameters],
  )

  const payload = useMemo<StrategyPayload | null>(() => definition ? ({
    strategy_name: definition.key,
    strategy_version: definition.version,
    exchange,
    symbol: 'BTC/USDT',
    timeframe,
    days,
    parameters: resolvedParameters,
    risk: { max_position_pct: maxPositionPct },
    execution: {
      initial_capital: initialCapital,
      fee_rate: feeRate,
      slippage_rate: slippageRate,
      signal_on: 'candle_close',
      execute_on: 'next_candle_open',
    },
  }) : null, [days, definition, exchange, feeRate, initialCapital, maxPositionPct, resolvedParameters, slippageRate, timeframe])
  const debouncedPreviewInput = useDebouncedValue(
    useMemo(() => ({ strategyKey, exchange, timeframe, parameters: resolvedParameters }), [exchange, resolvedParameters, strategyKey, timeframe]),
    350,
  )
  const preview = useQuery({
    queryKey: ['strategy-preview', debouncedPreviewInput],
    queryFn: () => previewStrategy(debouncedPreviewInput.strategyKey, {
      strategy_version: definition?.version,
      exchange: debouncedPreviewInput.exchange,
      symbol: 'BTC/USDT',
      timeframe: debouncedPreviewInput.timeframe,
      limit: 300,
      parameters: debouncedPreviewInput.parameters,
    }),
    enabled: Boolean(definition && Object.keys(debouncedPreviewInput.parameters).length),
    retry: false,
  })

  const saveConfig = useMutation({
    mutationFn: async () => {
      if (!payload) throw new Error('strategy unavailable')
      if (selectedConfigId) return createStrategyConfigVersion(selectedConfigId, payload)
      return createStrategyConfig(configName.trim() || 'Untitled strategy', payload)
    },
    onSuccess: (config) => {
      setSelectedConfigId(config.id)
      setConfigName(config.name)
      setNotice(t('strategy.savedNotice', { version: config.latest_version_number }))
      void queryClient.invalidateQueries({ queryKey: ['strategy-configs'] })
    },
  })
  const runCurrent = useMutation({
    mutationFn: async () => {
      if (!payload) throw new Error('strategy unavailable')
      return createBacktest(payload)
    },
    onSuccess: () => {
      setNotice(t('strategy.runQueued'))
      void queryClient.invalidateQueries({ queryKey: ['backtests'] })
    },
  })
  const runVersion = useMutation({
    mutationFn: ({ configId, version }: { configId: string; version: number }) => (
      runStrategyConfig(configId, version)
    ),
    onSuccess: () => {
      setNotice(t('strategy.versionRunQueued'))
      void queryClient.invalidateQueries({ queryKey: ['backtests'] })
    },
  })

  function selectStrategy(nextDefinition: StrategyDefinition) {
    setStrategyKey(nextDefinition.key)
    setParameters(defaultParameters(nextDefinition))
    setSelectedConfigId(null)
    setNotice('')
  }

  function loadVersion(config: StrategyConfig, version: StrategyConfigVersion) {
    setSelectedConfigId(config.id)
    setConfigName(config.name)
    setStrategyKey(version.strategy_name)
    setParameters(version.parameters)
    setExchange(version.exchange as 'binance' | 'okx')
    setTimeframe(version.timeframe as StrategyPayload['timeframe'])
    setDays(version.days)
    setInitialCapital(version.execution_config.initial_capital)
    setFeeRate(version.execution_config.fee_rate)
    setSlippageRate(version.execution_config.slippage_rate)
    setMaxPositionPct(version.risk_config.max_position_pct)
    setNotice(t('strategy.loadedVersion', { version: version.version_number }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const chartSettings = useMemo<MarketChartSettings>(() => ({
    volume: true,
    fastMa: false,
    slowMa: false,
    macd: false,
    signals: true,
    executions: true,
    fastWindow: 20,
    slowWindow: 60,
  }), [])
  const chartLabels = useMemo(() => ({
    open: t('data.open'), high: t('data.high'), low: t('data.low'), close: t('data.close'),
    volume: t('data.volume'), noCandles: t('strategy.previewEmpty'),
    buySignal: t('strategy.increaseSignal'), sellSignal: t('strategy.decreaseSignal'),
    buyExecution: t('strategy.increaseExecution'), sellExecution: t('strategy.decreaseExecution'),
  }), [t])
  const ignoreLoadEarlier = useCallback(() => undefined, [])

  return (
    <div className="animate-rise">
      <header className="relative overflow-hidden rounded-2xl border border-[#20222a] bg-[#111216] px-6 py-7 text-white shadow-[0_18px_60px_rgba(16,17,20,0.16)] sm:px-8">
        <div className="absolute -right-20 -top-28 size-72 rounded-full border border-white/10" />
        <div className="absolute -right-8 top-8 size-36 rounded-full border border-brand/50" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#a8aabd]">{t('strategy.eyebrow')}</p>
            <h1 className="mt-3 max-w-3xl text-3xl font-bold tracking-[-0.045em] sm:text-4xl">{t('strategy.workspaceTitle')}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#b6b8c5]">{t('strategy.workspaceDescription')}</p>
          </div>
          <div className="flex gap-6 text-xs text-[#a8aabd]">
            <span><b className="block text-xl text-white">{definitions.data?.length ?? 0}</b>{t('strategy.builtInCount')}</span>
            <span><b className="block text-xl text-white">{configs.data?.length ?? 0}</b>{t('strategy.savedCount')}</span>
            <span><b className="block text-xl text-[#a98aff]">UTC</b>{t('strategy.researchClock')}</span>
          </div>
        </div>
      </header>

      <section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {definitions.data?.map((item) => {
          const active = item.key === strategyKey
          const Icon = STRATEGY_ICONS[item.key as keyof typeof STRATEGY_ICONS] ?? FlaskConical
          const i18nKey = STRATEGY_I18N[item.key as keyof typeof STRATEGY_I18N]
          return (
            <button
              className={`group min-h-36 rounded-2xl border p-5 text-left transition-all ${active ? 'border-brand bg-[#f4f0ff] shadow-[0_8px_30px_rgba(113,50,245,0.13)]' : 'border-line bg-white hover:-translate-y-0.5 hover:border-[#aaa4bc]'}`}
              key={item.key}
              onClick={() => selectStrategy(item)}
              type="button"
            >
              <span className={`grid size-9 place-items-center rounded-xl ${active ? 'bg-brand text-white' : 'bg-[#f1f1f4] text-muted group-hover:text-ink'}`}><Icon size={17} /></span>
              <strong className="mt-4 block text-sm">{i18nKey ? t(`strategy.catalog.${i18nKey}.title`) : item.title}</strong>
              <span className="mt-1.5 block text-xs leading-5 text-muted">{i18nKey ? t(`strategy.catalog.${i18nKey}.description`) : item.description}</span>
            </button>
          )
        })}
      </section>

      <section className="mt-5 grid min-w-0 gap-5 2xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside className="research-card h-fit overflow-hidden">
          <div className="border-b border-line bg-[#fafafd] px-5 py-4">
            <div className="flex items-center justify-between"><span className="flex items-center gap-2 text-sm font-bold"><SlidersHorizontal size={16} className="text-brand" />{t('strategy.configuration')}</span><code className="text-[10px] text-muted">{definition?.version ?? '—'}</code></div>
          </div>
          <div className="space-y-6 p-5">
            <fieldset className="space-y-4">
              <legend className="mb-3 text-[11px] font-bold uppercase tracking-[0.1em] text-muted">01 · {t('strategy.marketScope')}</legend>
              <label className="grid gap-1.5 text-xs font-semibold">{t('strategy.configName')}<input className="field-control" maxLength={120} onChange={(event) => setConfigName(event.target.value)} value={configName} /></label>
              <div className="grid grid-cols-2 gap-3">
                <label className="grid gap-1.5 text-xs font-semibold">{t('data.exchange')}<select className="field-control" onChange={(event) => setExchange(event.target.value as 'binance' | 'okx')} value={exchange}><option value="binance">Binance</option><option value="okx">OKX</option></select></label>
                <label className="grid gap-1.5 text-xs font-semibold">{t('data.timeframe')}<select className="field-control" onChange={(event) => setTimeframe(event.target.value as StrategyPayload['timeframe'])} value={timeframe}>{definition?.data_requirements.timeframes.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
              </div>
              <label className="grid gap-1.5 text-xs font-semibold">{t('strategy.historyDays')}<input className="field-control" max="3650" min="1" onChange={(event) => setDays(Number(event.target.value))} type="number" value={days} /></label>
            </fieldset>

            <fieldset className="space-y-3 border-t border-line pt-5">
              <legend className="mb-3 text-[11px] font-bold uppercase tracking-[0.1em] text-muted">02 · {t('strategy.ruleParameters')}</legend>
              {Object.entries(definition?.parameters_schema.properties ?? {}).map(([key, schema]) => (
                <label className="grid gap-1.5 text-xs font-semibold" key={key}>
                  <span className="flex items-center justify-between"><span>{schema.title ?? key}</span><code className="font-normal text-muted">{key}</code></span>
                  <input className="field-control" max={schema.maximum} min={schema.minimum} onChange={(event) => setParameters((current) => ({ ...resolvedParameters, ...current, [key]: Number(event.target.value) }))} step={schema.type === 'integer' ? 1 : 'any'} type="number" value={resolvedParameters[key] ?? ''} />
                  {schema.description && <small className="font-normal leading-5 text-muted">{schema.description}</small>}
                </label>
              ))}
            </fieldset>

            <fieldset className="space-y-4 border-t border-line pt-5">
              <legend className="mb-3 text-[11px] font-bold uppercase tracking-[0.1em] text-muted">03 · {t('strategy.riskAndExecution')}</legend>
              <label className="grid gap-1.5 text-xs font-semibold">{t('strategy.maxPosition')}<div className="flex items-center gap-3"><input className="w-full accent-[#7132f5]" max="1" min="0.05" onChange={(event) => setMaxPositionPct(Number(event.target.value))} step="0.05" type="range" value={maxPositionPct} /><code className="w-12 text-right">{Math.round(maxPositionPct * 100)}%</code></div></label>
              <label className="grid gap-1.5 text-xs font-semibold">{t('strategy.initialCapital')}<input className="field-control" min="1" onChange={(event) => setInitialCapital(Number(event.target.value))} type="number" value={initialCapital} /></label>
              <div className="grid grid-cols-2 gap-3">
                <label className="grid gap-1.5 text-xs font-semibold">{t('strategy.feeRate')}<input className="field-control" min="0" onChange={(event) => setFeeRate(Number(event.target.value) / 100)} step="0.01" type="number" value={feeRate * 100} /></label>
                <label className="grid gap-1.5 text-xs font-semibold">{t('strategy.slippageRate')}<input className="field-control" min="0" onChange={(event) => setSlippageRate(Number(event.target.value) / 100)} step="0.01" type="number" value={slippageRate * 100} /></label>
              </div>
              <p className="flex gap-2 rounded-xl bg-[#f6f7f8] p-3 text-[11px] leading-5 text-muted"><ShieldCheck className="mt-0.5 shrink-0 text-success" size={14} />{t('strategy.nextOpenRule')}</p>
            </fieldset>

            {(saveConfig.error || runCurrent.error) && <p className="flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700"><AlertCircle className="shrink-0" size={15} />{t('strategy.actionError')}</p>}
            {notice && <p className="flex gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-success-dark"><Sparkles className="shrink-0" size={15} />{notice}</p>}
            <div className="grid gap-2 sm:grid-cols-2 2xl:grid-cols-1">
              <button className="button-primary" disabled={!payload || saveConfig.isPending} onClick={() => saveConfig.mutate()} type="button">{saveConfig.isPending ? <LoaderCircle className="animate-spin" size={16} /> : <Save size={16} />}{selectedConfigId ? t('strategy.saveNewVersion') : t('strategy.saveConfiguration')}</button>
              <button className="button-outline" disabled={!payload || runCurrent.isPending} onClick={() => runCurrent.mutate()} type="button">{runCurrent.isPending ? <LoaderCircle className="animate-spin" size={16} /> : <Play size={16} />}{t('strategy.runCurrent')}</button>
            </div>
          </div>
        </aside>

        <div className="min-w-0 space-y-5">
          <div className="research-card overflow-hidden">
            <div className="flex flex-col gap-3 border-b border-line px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div><p className="text-xs text-muted">BTC / USDT · {exchange.toUpperCase()} · {timeframe}</p><h2 className="mt-1 font-bold">{t('strategy.livePreview')}</h2></div>
              <div className="flex items-center gap-3 text-xs text-muted"><span className="inline-flex items-center gap-1.5"><span className="size-2 rounded-full bg-success" />{t('strategy.closedCandlesOnly')}</span><span>{preview.data?.candles.length ?? 0} K</span></div>
            </div>
            {preview.error && <div className="flex min-h-36 items-center justify-center gap-2 px-6 text-sm text-red-700"><AlertCircle size={17} />{t('strategy.previewError')}</div>}
            {!preview.error && (
              <MarketChart
                candles={preview.data?.candles ?? []}
                hasMore={false}
                labels={chartLabels}
                loading={preview.isPending}
                loadingEarlier={false}
                locale={language}
                onLoadEarlier={ignoreLoadEarlier}
                overlays={preview.data?.plots ?? []}
                settings={chartSettings}
                signals={preview.data?.signals ?? []}
              />
            )}
            <div className="grid gap-4 border-t border-line bg-[#fafafd] px-5 py-4 md:grid-cols-[1fr_auto_auto] md:items-center">
              <p className="text-xs leading-5 text-muted">{preview.data?.explanation ?? t('strategy.previewHint')}</p>
              <span className="text-xs"><b className="block text-sm">{preview.data?.warmup_bars ?? definition?.default_warmup_bars ?? '—'}</b>{t('strategy.warmupBars')}</span>
              <span className="text-xs"><b className="block text-sm">{preview.data?.signals.length ?? '—'}</b>{t('strategy.signalCount')}</span>
            </div>
          </div>

          <SavedConfigurations
            configs={configs.data ?? []}
            language={language}
            loading={configs.isPending}
            onLoad={loadVersion}
            onRun={(configId, version) => runVersion.mutate({ configId, version })}
            running={runVersion.isPending}
          />
        </div>
      </section>
    </div>
  )
}

function SavedConfigurations({
  configs,
  language,
  loading,
  onLoad,
  onRun,
  running,
}: {
  configs: StrategyConfig[]
  language: AppLanguage
  loading: boolean
  onLoad: (config: StrategyConfig, version: StrategyConfigVersion) => void
  onRun: (configId: string, version: number) => void
  running: boolean
}) {
  const { t } = useTranslation()
  const [openConfigId, setOpenConfigId] = useState<string | null>(null)
  const config = configs.find((item) => item.id === openConfigId) ?? configs[0]
  const compareVersions = config?.versions.slice(0, 2) ?? []

  return (
    <div className="research-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <div className="flex items-center gap-2"><GitBranch className="text-brand" size={17} /><div><h2 className="text-sm font-bold">{t('strategy.savedConfigurations')}</h2><p className="mt-0.5 text-xs text-muted">{t('strategy.immutableHint')}</p></div></div>
        <span className="rounded-lg bg-[#f1f1f4] px-2 py-1 text-[10px] text-muted">{configs.length}</span>
      </div>
      {loading && <div className="grid min-h-36 place-items-center text-sm text-muted"><LoaderCircle className="animate-spin" size={18} /></div>}
      {!loading && configs.length === 0 && <div className="grid min-h-36 place-items-center px-6 text-center text-sm text-muted">{t('strategy.noSavedConfigurations')}</div>}
      {configs.length > 0 && (
        <div className="grid min-w-0 lg:grid-cols-[240px_minmax(0,1fr)]">
          <div className="border-b border-line bg-[#fafafd] p-3 lg:border-b-0 lg:border-r">
            {configs.map((item) => (
              <button className={`mb-1 flex w-full items-center justify-between rounded-xl px-3 py-3 text-left text-sm ${config?.id === item.id ? 'bg-white font-semibold shadow-sm' : 'text-muted hover:bg-white'}`} key={item.id} onClick={() => setOpenConfigId(item.id)} type="button"><span className="truncate">{item.name}<small className="mt-1 block font-normal text-muted">v{item.latest_version_number}</small></span><ChevronRight size={15} /></button>
            ))}
          </div>
          {config && <div className="min-w-0 p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><h3 className="font-bold">{config.name}</h3><p className="mt-1 text-xs text-muted">{t('strategy.updatedAt')} {formatDateTime(config.updated_at, language)}</p></div><span className="inline-flex w-fit items-center gap-1.5 rounded-lg bg-[#f0ecfe] px-2.5 py-1 text-xs text-brand-deep"><GitBranch size={12} />{config.versions.length} versions</span></div>
            <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[680px] border-collapse text-left text-xs">
                <thead><tr className="border-b border-line text-muted"><th className="pb-3 font-medium">{t('strategy.version')}</th><th className="pb-3 font-medium">{t('strategy.strategy')}</th><th className="pb-3 font-medium">{t('strategy.parameters')}</th><th className="pb-3 font-medium">{t('strategy.risk')}</th><th className="pb-3 font-medium">{t('strategy.createdAt')}</th><th className="pb-3" /></tr></thead>
                <tbody>{config.versions.map((version) => <tr className="border-b border-line/70 last:border-0" key={version.id}><td className="py-3 font-bold">v{version.version_number}</td><td className="py-3">{version.strategy_name}<small className="block text-muted">{version.exchange} · {version.timeframe} · {version.days}d</small></td><td className="py-3"><code>{Object.entries(version.parameters).map(([key, value]) => `${key}=${value}`).join(' · ')}</code></td><td className="py-3">{Math.round(version.risk_config.max_position_pct * 100)}%</td><td className="py-3 text-muted">{formatDateTime(version.created_at, language)}</td><td className="py-3 text-right"><div className="inline-flex gap-1"><button className="rounded-lg border border-line px-2.5 py-1.5 font-semibold hover:border-brand hover:text-brand" onClick={() => onLoad(config, version)} type="button">{t('strategy.load')}</button><button className="rounded-lg bg-ink px-2.5 py-1.5 font-semibold text-white disabled:opacity-50" disabled={running} onClick={() => onRun(config.id, version.version_number)} type="button">{t('strategy.backtest')}</button></div></td></tr>)}</tbody>
              </table>
            </div>
            {compareVersions.length === 2 && <div className="mt-5 rounded-xl border border-line bg-[#fafafd] p-4"><div className="flex items-center gap-2 text-xs font-bold"><BarChart3 className="text-brand" size={15} />{t('strategy.latestVersionDiff')}</div><div className="mt-3 grid gap-2 text-xs sm:grid-cols-3"><DiffItem label={t('strategy.parameters')} left={JSON.stringify(compareVersions[1].parameters)} right={JSON.stringify(compareVersions[0].parameters)} /><DiffItem label={t('strategy.maxPosition')} left={`${compareVersions[1].risk_config.max_position_pct * 100}%`} right={`${compareVersions[0].risk_config.max_position_pct * 100}%`} /><DiffItem label={t('strategy.tradingCost')} left={`${(compareVersions[1].execution_config.fee_rate + compareVersions[1].execution_config.slippage_rate) * 100}%`} right={`${(compareVersions[0].execution_config.fee_rate + compareVersions[0].execution_config.slippage_rate) * 100}%`} /></div></div>}
          </div>}
        </div>
      )}
    </div>
  )
}

function DiffItem({ label, left, right }: { label: string; left: string; right: string }) {
  const changed = left !== right
  return <div className={`rounded-lg border p-3 ${changed ? 'border-brand/30 bg-white' : 'border-transparent'}`}><span className="text-muted">{label}</span><code className="mt-1 block break-all">v-1 {left}</code><code className={changed ? 'mt-1 block break-all text-brand-deep' : 'mt-1 block break-all'}>latest {right}</code></div>
}
