import { useCallback, useEffect, useMemo, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { Activity, ChevronDown, RotateCcw, Settings2, Wifi } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { currentLanguage } from '../../i18n'
import type { MarketStreamRecord } from '../../types'
import { getMarketChartPage } from './api'
import { MarketChart } from './MarketChart'
import type {
  MarketCandle,
  MarketChartSettings,
  MarketExchange,
  MarketSignal,
  MarketTimeframe,
} from './types'

const TIMEFRAMES: MarketTimeframe[] = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
const DEFAULT_SETTINGS: MarketChartSettings = {
  volume: true,
  fastMa: true,
  slowMa: true,
  macd: false,
  signals: false,
  executions: true,
  fastWindow: 20,
  slowWindow: 60,
}
const STORAGE_KEY = 'qwr-market-chart-settings-v1'

interface MarketChartWorkspaceProps {
  exchange: MarketExchange
  timeframe: MarketTimeframe
  streams: MarketStreamRecord[]
  onExchangeChange: (exchange: MarketExchange) => void
  onTimeframeChange: (timeframe: MarketTimeframe) => void
}

function readSettings() {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return value ? { ...DEFAULT_SETTINGS, ...JSON.parse(value) as Partial<MarketChartSettings> } : DEFAULT_SETTINGS
  } catch {
    return DEFAULT_SETTINGS
  }
}

function dedupeCandles(pages: MarketCandle[][]) {
  const values = new Map<string, MarketCandle>()
  pages.flat().forEach((candle) => values.set(candle.open_time, candle))
  return [...values.values()].sort((left, right) => left.open_time.localeCompare(right.open_time))
}

function dedupeSignals(pages: MarketSignal[][]) {
  const values = new Map<string, MarketSignal>()
  pages.flat().forEach((signal) => values.set(`${signal.execution_time}-${signal.side}`, signal))
  return [...values.values()].sort((left, right) => left.execution_time.localeCompare(right.execution_time))
}

export function MarketChartWorkspace({
  exchange,
  timeframe,
  streams,
  onExchangeChange,
  onTimeframeChange,
}: MarketChartWorkspaceProps) {
  const { t } = useTranslation()
  const locale = currentLanguage()
  const [settings, setSettings] = useState<MarketChartSettings>(readSettings)
  const [mobileSettingsOpen, setMobileSettingsOpen] = useState(false)
  const validWindows = settings.fastWindow >= 2 && settings.fastWindow < settings.slowWindow && settings.slowWindow <= 500
  const includeSignals = settings.signals && validWindows
  const selectedStream = streams.find((stream) => stream.exchange === exchange && stream.timeframe === timeframe)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  }, [settings])

  const chartQuery = useInfiniteQuery({
    queryKey: ['market-chart', exchange, timeframe, settings.fastWindow, settings.slowWindow, includeSignals],
    queryFn: ({ pageParam }) => getMarketChartPage({
      exchange,
      timeframe,
      before: pageParam,
      fastWindow: settings.fastWindow,
      slowWindow: settings.slowWindow,
      includeSignals,
    }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.candles.next_before ?? undefined,
    refetchInterval: 15_000,
  })

  const candles = useMemo(
    () => dedupeCandles(chartQuery.data?.pages.map((page) => page.candles.items) ?? []),
    [chartQuery.data],
  )
  const signals = useMemo(
    () => dedupeSignals(chartQuery.data?.pages.map((page) => page.signals) ?? []),
    [chartQuery.data],
  )
  const loadEarlier = useCallback(() => {
    if (chartQuery.hasNextPage && !chartQuery.isFetchingNextPage) void chartQuery.fetchNextPage()
  }, [chartQuery])

  function updateSetting<K extends keyof MarketChartSettings>(key: K, value: MarketChartSettings[K]) {
    setSettings((current) => ({ ...current, [key]: value }))
  }

  const settingsPanel = (
    <aside className="border-t border-line bg-[#fafafd] p-5 xl:border-l xl:border-t-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2"><Settings2 className="text-brand" size={17} /><h3 className="text-sm font-bold">{t('data.chartSettings')}</h3></div>
        <button className="rounded-lg p-1.5 text-muted transition hover:bg-white hover:text-ink" onClick={() => setSettings(DEFAULT_SETTINGS)} title={t('data.resetChart')} type="button"><RotateCcw size={15} /></button>
      </div>
      <p className="mt-2 text-xs leading-5 text-muted">{t('data.chartSettingsHint')}</p>

      <div className="mt-5 space-y-2">
        <SettingToggle checked={settings.volume} label={t('data.volume')} onChange={(value) => updateSetting('volume', value)} swatch="#7b8099" />
        <SettingToggle checked={settings.fastMa} label={`${t('data.fastMa')} · MA${settings.fastWindow}`} onChange={(value) => updateSetting('fastMa', value)} swatch="#4c6fff" />
        <SettingToggle checked={settings.slowMa} label={`${t('data.slowMa')} · MA${settings.slowWindow}`} onChange={(value) => updateSetting('slowMa', value)} swatch="#ed9b3b" />
        <SettingToggle checked={settings.macd} label="MACD (12, 26, 9)" onChange={(value) => updateSetting('macd', value)} swatch="#7132f5" />
        <SettingToggle checked={settings.signals} label={t('data.strategySignals')} onChange={(value) => updateSetting('signals', value)} swatch="#0f9d72" />
        <div className="pl-5">
          <SettingToggle checked={settings.executions} disabled={!settings.signals} label={t('data.executionMarks')} onChange={(value) => updateSetting('executions', value)} swatch="#101114" />
        </div>
      </div>

      <div className="mt-6 border-t border-line pt-5">
        <p className="text-[11px] font-bold uppercase tracking-[0.1em] text-muted">{t('data.maParameters')}</p>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <NumberField label={t('data.fastPeriod')} max={499} min={2} value={settings.fastWindow} onChange={(value) => updateSetting('fastWindow', value)} />
          <NumberField label={t('data.slowPeriod')} max={500} min={3} value={settings.slowWindow} onChange={(value) => updateSetting('slowWindow', value)} />
        </div>
        {!validWindows && <p className="mt-2 text-xs leading-5 text-[#b64545]">{t('data.invalidMaWindows')}</p>}
        <p className="mt-4 rounded-xl border border-[#e6e1fa] bg-[#f6f3ff] p-3 text-xs leading-5 text-[#5741a8]">{t('data.signalTimingNote')}</p>
      </div>
    </aside>
  )

  return (
    <section className="mt-8 overflow-hidden rounded-2xl border border-line bg-white shadow-[0_10px_40px_rgba(16,17,20,0.05)]">
      <div className="border-b border-line bg-white px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f0ebff] text-brand"><Activity size={20} /></div>
            <div className="min-w-0"><div className="flex items-center gap-2"><h2 className="truncate font-bold">BTC / USDT</h2><span className="rounded-md bg-[#f2f2f5] px-1.5 py-0.5 text-[10px] font-bold text-muted">SPOT</span></div><p className="mt-0.5 text-xs text-muted">{t('data.chartDescription')}</p></div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="relative">
              <span className="sr-only">{t('data.exchange')}</span>
              <select className="h-9 appearance-none rounded-lg border border-line bg-white py-0 pl-3 pr-8 text-xs font-semibold uppercase outline-none focus:border-brand" value={exchange} onChange={(event) => onExchangeChange(event.target.value as MarketExchange)}><option value="binance">BINANCE</option><option value="okx">OKX</option></select>
              <ChevronDown className="pointer-events-none absolute right-2 top-2.5 text-muted" size={14} />
            </label>
            <div className="flex rounded-lg border border-line bg-[#fafafd] p-0.5">
              {TIMEFRAMES.map((value) => <button className={`rounded-md px-2.5 py-1.5 text-xs font-semibold transition ${value === timeframe ? 'bg-ink text-white shadow-sm' : 'text-muted hover:bg-white hover:text-ink'}`} key={value} onClick={() => onTimeframeChange(value)} type="button">{value}</button>)}
            </div>
            <button className="flex h-9 items-center gap-2 rounded-lg border border-line px-3 text-xs font-semibold text-muted xl:hidden" onClick={() => setMobileSettingsOpen((value) => !value)} type="button"><Settings2 size={15} />{t('data.indicators')}</button>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted">
          <span className="inline-flex items-center gap-1.5"><Wifi className={selectedStream?.status === 'live' ? 'text-success' : 'text-silver'} size={13} />{selectedStream?.status === 'live' ? t('data.liveClosedCandles') : t('data.closedCandles')}</span>
          <span>{t('data.rowsLoaded', { count: candles.length })}</span>
          <span>UTC</span>
          {chartQuery.isError && <span className="font-medium text-[#b64545]">{t('data.chartError')}</span>}
        </div>
      </div>

      <div className="grid min-w-0 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div className="min-w-0">
          <MarketChart
            candles={candles}
            hasMore={Boolean(chartQuery.hasNextPage)}
            labels={{
              open: t('data.open'), high: t('data.high'), low: t('data.low'), close: t('data.close'), volume: t('data.volume'),
              noCandles: t('data.noCandles'), buySignal: t('data.buySignal'), sellSignal: t('data.sellSignal'),
              buyExecution: t('data.buyExecution'), sellExecution: t('data.sellExecution'),
            }}
            loading={chartQuery.isLoading}
            loadingEarlier={chartQuery.isFetchingNextPage}
            locale={locale}
            onLoadEarlier={loadEarlier}
            settings={settings}
            signals={signals}
          />
          {chartQuery.hasNextPage && <div className="border-t border-line px-5 py-3 text-center"><button className="text-xs font-semibold text-brand hover:text-brand-deep" disabled={chartQuery.isFetchingNextPage} onClick={loadEarlier} type="button">{chartQuery.isFetchingNextPage ? t('data.loadingEarlier') : t('data.loadEarlier')}</button></div>}
        </div>
        <div className="hidden xl:block">{settingsPanel}</div>
        {mobileSettingsOpen && <div className="xl:hidden">{settingsPanel}</div>}
      </div>
    </section>
  )
}

function SettingToggle({ checked, disabled = false, label, onChange, swatch }: { checked: boolean; disabled?: boolean; label: string; onChange: (value: boolean) => void; swatch: string }) {
  return <label className={`flex cursor-pointer items-center justify-between rounded-lg px-2 py-2 text-xs transition hover:bg-white ${disabled ? 'cursor-not-allowed opacity-40' : ''}`}><span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full" style={{ background: swatch }} />{label}</span><input checked={checked} className="sr-only" disabled={disabled} onChange={(event) => onChange(event.target.checked)} type="checkbox" /><span className={`relative h-5 w-9 rounded-full transition ${checked ? 'bg-brand' : 'bg-[#d3d4dd]'}`}><span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition ${checked ? 'left-[18px]' : 'left-0.5'}`} /></span></label>
}

function NumberField({ label, max, min, onChange, value }: { label: string; max: number; min: number; onChange: (value: number) => void; value: number }) {
  return <label><span className="text-[11px] text-muted">{label}</span><input className="mt-1 w-full rounded-lg border border-line bg-white px-2.5 py-2 text-sm font-semibold outline-none focus:border-brand" max={max} min={min} onChange={(event) => onChange(Number(event.target.value))} type="number" value={value} /></label>
}
