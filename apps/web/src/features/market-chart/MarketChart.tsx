import { useEffect, useMemo, useRef, useState } from 'react'
import { LoaderCircle } from 'lucide-react'
import type {
  CandlestickData,
  HistogramData,
  LineData,
  SeriesMarker,
  Time,
  UTCTimestamp,
} from 'lightweight-charts'

import { macd, simpleMovingAverage } from './indicators'
import type { MarketCandle, MarketChartSettings, MarketSignal } from './types'

interface MarketChartProps {
  candles: MarketCandle[]
  signals: MarketSignal[]
  settings: MarketChartSettings
  locale: string
  loading: boolean
  loadingEarlier: boolean
  hasMore: boolean
  labels: {
    open: string
    high: string
    low: string
    close: string
    volume: string
    noCandles: string
    buySignal: string
    sellSignal: string
    buyExecution: string
    sellExecution: string
  }
  onLoadEarlier: () => void
}

interface OhlcSnapshot {
  open: number
  high: number
  low: number
  close: number
}

function unixTime(value: string) {
  return Math.floor(Date.parse(value) / 1000) as UTCTimestamp
}

function formatPrice(value: number, locale: string) {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value)
}

export function MarketChart({
  candles,
  signals,
  settings,
  locale,
  loading,
  loadingEarlier,
  hasMore,
  labels,
  onLoadEarlier,
}: MarketChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const visibleRangeRef = useRef<{ from: Time; to: Time } | null>(null)
  const loadingGuardRef = useRef(false)
  const [snapshot, setSnapshot] = useState<OhlcSnapshot | null>(null)

  const candleData = useMemo<CandlestickData<UTCTimestamp>[]>(() => candles.map((candle) => ({
    time: unixTime(candle.open_time),
    open: Number(candle.open),
    high: Number(candle.high),
    low: Number(candle.low),
    close: Number(candle.close),
  })), [candles])

  const latest = snapshot ?? (candleData.at(-1) ?? null)

  useEffect(() => {
    loadingGuardRef.current = loadingEarlier
  }, [loadingEarlier])

  useEffect(() => {
    const container = containerRef.current
    if (!container || candleData.length === 0) return undefined
    let disposed = false
    let cleanup = () => undefined

    void import('lightweight-charts').then((charts) => {
      if (disposed) return
      const chart = charts.createChart(container, {
        autoSize: true,
        layout: {
          background: { type: charts.ColorType.Solid, color: '#ffffff' },
          textColor: '#686b82',
          fontFamily: 'IBM Plex Sans, Helvetica Neue, sans-serif',
          fontSize: 12,
          attributionLogo: false,
          panes: {
            separatorColor: '#dedee5',
            separatorHoverColor: 'rgba(113, 50, 245, 0.18)',
            enableResize: true,
          },
        },
        grid: {
          vertLines: { color: '#f0f0f4' },
          horzLines: { color: '#f0f0f4' },
        },
        crosshair: { mode: charts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#dedee5' },
        timeScale: {
          borderColor: '#dedee5',
          timeVisible: true,
          secondsVisible: false,
          rightOffset: 6,
          barSpacing: 8,
          minBarSpacing: 2,
        },
        localization: { locale },
      })
      const candleSeries = chart.addSeries(charts.CandlestickSeries, {
        upColor: '#0f9d72',
        downColor: '#e05d5d',
        borderVisible: false,
        wickUpColor: '#0f9d72',
        wickDownColor: '#e05d5d',
        priceLineVisible: true,
        lastValueVisible: true,
      })
      candleSeries.setData(candleData)

      if (settings.fastMa) {
        const series = chart.addSeries(charts.LineSeries, {
          color: '#4c6fff',
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        })
        series.setData(simpleMovingAverage(candles, settings.fastWindow).map<LineData<UTCTimestamp>>((point) => ({
          time: unixTime(point.time), value: point.value,
        })))
      }
      if (settings.slowMa) {
        const series = chart.addSeries(charts.LineSeries, {
          color: '#ed9b3b',
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        })
        series.setData(simpleMovingAverage(candles, settings.slowWindow).map<LineData<UTCTimestamp>>((point) => ({
          time: unixTime(point.time), value: point.value,
        })))
      }

      let nextPane = 1
      if (settings.volume) {
        const volumeSeries = chart.addSeries(charts.HistogramSeries, {
          priceFormat: { type: 'volume' },
          priceLineVisible: false,
          lastValueVisible: false,
        }, nextPane)
        volumeSeries.setData(candles.map<HistogramData<UTCTimestamp>>((candle) => ({
          time: unixTime(candle.open_time),
          value: Number(candle.volume),
          color: Number(candle.close) >= Number(candle.open) ? 'rgba(15, 157, 114, 0.46)' : 'rgba(224, 93, 93, 0.44)',
        })))
        nextPane += 1
      }

      if (settings.macd) {
        const points = macd(candles)
        const macdSeries = chart.addSeries(charts.LineSeries, {
          color: '#4c6fff', lineWidth: 2, priceLineVisible: false, lastValueVisible: false,
        }, nextPane)
        const signalSeries = chart.addSeries(charts.LineSeries, {
          color: '#ed9b3b', lineWidth: 2, priceLineVisible: false, lastValueVisible: false,
        }, nextPane)
        const histogramSeries = chart.addSeries(charts.HistogramSeries, {
          priceLineVisible: false, lastValueVisible: false, base: 0,
        }, nextPane)
        macdSeries.setData(points.map((point) => ({ time: unixTime(point.time), value: point.value })))
        signalSeries.setData(points.map((point) => ({ time: unixTime(point.time), value: point.signal })))
        histogramSeries.setData(points.map((point) => ({
          time: unixTime(point.time),
          value: point.histogram,
          color: point.histogram >= 0 ? 'rgba(15, 157, 114, 0.52)' : 'rgba(224, 93, 93, 0.5)',
        })))
      }

      const availableTimes = new Set(candleData.map((candle) => candle.time))
      const markers: SeriesMarker<UTCTimestamp>[] = signals.flatMap((signal) => {
        const result: SeriesMarker<UTCTimestamp>[] = []
        const signalTime = unixTime(signal.signal_time)
        const executionTime = unixTime(signal.execution_time)
        if (settings.signals && availableTimes.has(signalTime)) {
          result.push({
            time: signalTime,
            position: signal.side === 'buy' ? 'belowBar' : 'aboveBar',
            color: signal.side === 'buy' ? '#0f9d72' : '#e05d5d',
            shape: 'circle',
            text: signal.side === 'buy' ? labels.buySignal : labels.sellSignal,
          })
        }
        if (settings.signals && settings.executions && availableTimes.has(executionTime)) {
          result.push({
            time: executionTime,
            position: signal.side === 'buy' ? 'belowBar' : 'aboveBar',
            color: signal.side === 'buy' ? '#0f9d72' : '#e05d5d',
            shape: signal.side === 'buy' ? 'arrowUp' : 'arrowDown',
            text: signal.side === 'buy' ? labels.buyExecution : labels.sellExecution,
          })
        }
        return result
      }).sort((left, right) => Number(left.time) - Number(right.time))
      if (markers.length) charts.createSeriesMarkers(candleSeries, markers)

      const panes = chart.panes()
      panes[0]?.setStretchFactor(4)
      if (settings.volume) panes[1]?.setStretchFactor(0.9)
      if (settings.macd) panes[nextPane]?.setStretchFactor(1.35)

      const handleCrosshair = (param: Parameters<typeof chart.subscribeCrosshairMove>[0] extends (event: infer E) => void ? E : never) => {
        const value = param.seriesData.get(candleSeries) as CandlestickData<UTCTimestamp> | undefined
        if (value && 'open' in value) setSnapshot(value)
        else setSnapshot(null)
      }
      const handleLogicalRange = (range: { from: number; to: number } | null) => {
        if (range && range.from < 24 && hasMore && !loadingGuardRef.current) {
          loadingGuardRef.current = true
          onLoadEarlier()
        }
      }
      chart.subscribeCrosshairMove(handleCrosshair)
      chart.timeScale().subscribeVisibleLogicalRangeChange(handleLogicalRange)
      if (visibleRangeRef.current) chart.timeScale().setVisibleRange(visibleRangeRef.current)
      else chart.timeScale().fitContent()

      cleanup = () => {
        visibleRangeRef.current = chart.timeScale().getVisibleRange()
        chart.unsubscribeCrosshairMove(handleCrosshair)
        chart.timeScale().unsubscribeVisibleLogicalRangeChange(handleLogicalRange)
        chart.remove()
      }
    })

    return () => {
      disposed = true
      cleanup()
    }
  }, [candleData, candles, hasMore, labels, locale, onLoadEarlier, settings, signals])

  if (loading && candles.length === 0) {
    return <div className="flex h-[560px] items-center justify-center text-sm text-muted"><LoaderCircle className="mr-2 animate-spin" size={18} />Loading market data</div>
  }
  if (candles.length === 0) {
    return <div className="flex h-[560px] items-center justify-center text-sm text-muted">{labels.noCandles}</div>
  }

  return (
    <div className="relative min-w-0 bg-white">
      <div className="pointer-events-none absolute left-4 top-3 z-10 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg bg-white/88 px-2 py-1 text-[11px] shadow-sm backdrop-blur sm:left-5 sm:text-xs">
        {latest && <>
          <span><b className="font-medium text-muted">{labels.open}</b> {formatPrice(latest.open, locale)}</span>
          <span><b className="font-medium text-muted">{labels.high}</b> <span className="text-success-dark">{formatPrice(latest.high, locale)}</span></span>
          <span><b className="font-medium text-muted">{labels.low}</b> <span className="text-[#b64545]">{formatPrice(latest.low, locale)}</span></span>
          <span><b className="font-medium text-muted">{labels.close}</b> {formatPrice(latest.close, locale)}</span>
        </>}
      </div>
      {loadingEarlier && <div className="absolute left-1/2 top-14 z-10 -translate-x-1/2 rounded-full border border-line bg-white px-3 py-1 text-xs text-muted shadow-sm"><LoaderCircle className="mr-1 inline animate-spin" size={13} />Loading</div>}
      <div className="h-[560px] w-full" ref={containerRef} />
    </div>
  )
}
