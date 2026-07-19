import type { MarketCandle } from './types'

export interface TimedValue {
  time: string
  value: number
}

export interface MacdValue extends TimedValue {
  signal: number
  histogram: number
}

export function simpleMovingAverage(candles: MarketCandle[], period: number): TimedValue[] {
  if (period < 1) return []
  const result: TimedValue[] = []
  let rollingTotal = 0

  candles.forEach((candle, index) => {
    rollingTotal += Number(candle.close)
    if (index >= period) rollingTotal -= Number(candles[index - period].close)
    if (index >= period - 1) {
      result.push({ time: candle.open_time, value: rollingTotal / period })
    }
  })
  return result
}

function exponentialMovingAverage(values: number[], period: number) {
  const result = Array<number | null>(values.length).fill(null)
  if (period < 1 || values.length < period) return result

  const multiplier = 2 / (period + 1)
  let previous = values.slice(0, period).reduce((sum, value) => sum + value, 0) / period
  result[period - 1] = previous
  for (let index = period; index < values.length; index += 1) {
    previous = (values[index] - previous) * multiplier + previous
    result[index] = previous
  }
  return result
}

export function macd(candles: MarketCandle[]): MacdValue[] {
  const closes = candles.map((candle) => Number(candle.close))
  const fast = exponentialMovingAverage(closes, 12)
  const slow = exponentialMovingAverage(closes, 26)
  const macdLine = closes.map((_, index) =>
    fast[index] === null || slow[index] === null ? null : fast[index]! - slow[index]!,
  )
  const availableMacd = macdLine.filter((value): value is number => value !== null)
  const availableSignal = exponentialMovingAverage(availableMacd, 9)
  let signalIndex = 0

  return macdLine.flatMap((value, index) => {
    if (value === null) return []
    const signal = availableSignal[signalIndex]
    signalIndex += 1
    if (signal === null) return []
    return [{
      time: candles[index].open_time,
      value,
      signal,
      histogram: value - signal,
    }]
  })
}
