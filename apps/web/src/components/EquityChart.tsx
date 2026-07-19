import type { ECharts } from 'echarts/core'
import { useEffect, useRef } from 'react'

interface EquityChartProps {
  compact?: boolean
}

const strategy = [1000, 1012, 1006, 1038, 1054, 1046, 1088, 1096, 1125, 1117, 1154, 1179]
const benchmark = [1000, 991, 1009, 1022, 1003, 1028, 1014, 1038, 1021, 1047, 1036, 1052]

export function EquityChart({ compact = false }: EquityChartProps) {
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!elementRef.current) return
    let chart: ECharts | undefined
    let cancelled = false

    void import('./chartRuntime').then(({ echarts }) => {
      if (cancelled || !elementRef.current) return
      chart = echarts.init(elementRef.current)
      chart.setOption({
      animationDuration: 700,
      grid: { top: 18, right: 8, bottom: 20, left: compact ? 8 : 42, containLabel: false },
      tooltip: {
        trigger: 'axis',
        borderColor: '#dedee5',
        backgroundColor: '#ffffff',
        textStyle: { color: '#101114', fontFamily: 'IBM Plex Sans', fontSize: 12 },
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['01', '04', '07', '10', '13', '16', '19', '22', '25', '28', '31', '34'],
        axisLine: { lineStyle: { color: '#dedee5' } },
        axisTick: { show: false },
        axisLabel: { show: !compact, color: '#9497a9' },
      },
      yAxis: {
        type: 'value',
        min: 960,
        axisLabel: { show: !compact, color: '#9497a9' },
        splitLine: { lineStyle: { color: '#efeff3' } },
      },
      series: [
        {
          type: 'line',
          data: benchmark,
          symbol: 'none',
          smooth: 0.28,
          lineStyle: { color: '#b9bbc7', width: 2 },
        },
        {
          type: 'line',
          data: strategy,
          symbol: 'none',
          smooth: 0.28,
          lineStyle: { color: '#7132f5', width: 3 },
          areaStyle: { color: 'rgba(113, 50, 245, 0.08)' },
        },
      ],
      })
    })

    const resize = () => chart?.resize()
    window.addEventListener('resize', resize)
    return () => {
      cancelled = true
      window.removeEventListener('resize', resize)
      chart?.dispose()
    }
  }, [compact])

  return <div className={compact ? 'h-40 w-full' : 'h-64 w-full'} ref={elementRef} />
}
