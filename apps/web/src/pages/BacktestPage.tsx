import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Beaker, CheckCircle2, Clock3, LoaderCircle, Play, RefreshCw } from 'lucide-react'
import { useState, type FormEvent } from 'react'

import { createBacktest, listBacktests } from '../features/backtests/api'
import { formatDateTime, formatPercent } from '../lib/format'

export function BacktestPage() {
  const [fastWindow, setFastWindow] = useState(20)
  const [slowWindow, setSlowWindow] = useState(60)
  const [days, setDays] = useState(365)
  const [formError, setFormError] = useState('')
  const queryClient = useQueryClient()
  const runs = useQuery({ queryKey: ['backtests'], queryFn: listBacktests, refetchInterval: 5000 })
  const createRun = useMutation({
    mutationFn: createBacktest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['backtests'] }),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    setFormError('')
    if (fastWindow >= slowWindow) {
      setFormError('短期均线必须小于长期均线。')
      return
    }
    createRun.mutate({
      strategy_name: 'ma_cross_long_only',
      symbol: 'BTC/USDT',
      timeframe: '1d',
      days,
      parameters: { fast_window: fastWindow, slow_window: slowWindow, fee_rate: 0.001, slippage_rate: 0.0005 },
    })
  }

  return (
    <div className="animate-rise">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="eyebrow">Backtest queue</p><h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">回测任务</h1><p className="mt-3 text-sm text-muted">用同一份数据、同一套规则，对比策略与买入持有。</p></div>
        <button className="button-outline w-fit" onClick={() => runs.refetch()} type="button"><RefreshCw size={16} />刷新结果</button>
      </div>

      <section className="mt-8 grid gap-5 xl:grid-cols-[0.74fr_1.26fr]">
        <form className="research-card h-fit p-6 sm:p-7" onSubmit={submit}>
          <div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><Beaker size={19} /></span><div><p className="text-xs text-muted">New experiment</p><h2 className="font-bold">现货多头双均线</h2></div></div>
          <div className="mt-6 grid gap-5">
            <label className="grid gap-2 text-sm font-semibold">交易对<input className="field-control text-muted" disabled value="BTC/USDT" /></label>
            <div className="grid grid-cols-2 gap-4">
              <label className="grid gap-2 text-sm font-semibold">短期均线<input className="field-control" min="2" onChange={(event) => setFastWindow(Number(event.target.value))} type="number" value={fastWindow} /></label>
              <label className="grid gap-2 text-sm font-semibold">长期均线<input className="field-control" min="3" onChange={(event) => setSlowWindow(Number(event.target.value))} type="number" value={slowWindow} /></label>
            </div>
            <label className="grid gap-2 text-sm font-semibold">历史范围<select className="field-control" onChange={(event) => setDays(Number(event.target.value))} value={days}><option value={300}>最近 300 天</option><option value={365}>最近 365 天</option><option value={730}>最近 730 天</option></select></label>
            <div className="rounded-xl bg-[#f8f8fb] p-4 text-xs leading-6 text-muted"><p>手续费：0.10% / 次</p><p>滑点假设：0.05% / 次</p><p>执行时点：信号出现后的下一根 K 线</p></div>
          </div>
          {(formError || createRun.error) && <p className="mt-4 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700"><AlertCircle className="shrink-0" size={15} />{formError || createRun.error?.message}</p>}
          <button className="button-primary mt-6 w-full" disabled={createRun.isPending} type="submit">{createRun.isPending ? <LoaderCircle className="animate-spin" size={17} /> : <Play size={17} />}{createRun.isPending ? '正在创建' : '运行回测'}</button>
        </form>

        <div className="research-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-line px-5 py-5 sm:px-7"><div><h2 className="font-bold">实验记录</h2><p className="mt-1 text-xs text-muted">MySQL 保存元数据，完整结果写入研究产物目录</p></div><span className="text-xs text-muted">{runs.data?.length ?? 0} 条</span></div>
          <div className="divide-y divide-line">
            {runs.data?.map((run) => {
              const returnValue = run.summary?.strategy_total_return
              const drawdown = run.summary?.strategy_max_drawdown
              return (
                <article className="grid gap-4 px-5 py-5 sm:grid-cols-[1.15fr_0.8fr_auto] sm:items-center sm:px-7" key={run.id}>
                  <div><div className="flex items-center gap-2"><strong className="text-sm">MA {String(run.parameters.fast_window)} / {String(run.parameters.slow_window)}</strong><StatusBadge status={run.status} /></div><p className="mt-1.5 text-xs text-muted">BTC/USDT · 1d · {formatDateTime(run.created_at)}</p></div>
                  <div className="grid grid-cols-2 gap-4 text-sm"><span><small className="block text-xs text-muted">累计收益</small><strong className="mt-1 block">{returnValue === undefined ? '—' : formatPercent(returnValue)}</strong></span><span><small className="block text-xs text-muted">最大回撤</small><strong className="mt-1 block">{drawdown === undefined ? '—' : formatPercent(drawdown)}</strong></span></div>
                  <code className="text-[11px] text-silver">{run.id.slice(0, 8)}</code>
                  {run.error_message && <p className="text-xs text-red-700 sm:col-span-3">{run.error_message}</p>}
                </article>
              )
            })}
            {!runs.isPending && !runs.data?.length && <div className="grid min-h-64 place-items-center px-5 text-center"><div><Beaker className="mx-auto text-silver" size={30} /><p className="mt-4 text-sm font-semibold">还没有实验记录</p><p className="mt-2 text-xs text-muted">设置左侧参数，运行第一轮历史回测。</p></div></div>}
            {runs.isPending && <div className="grid min-h-64 place-items-center text-sm text-muted"><span className="flex items-center gap-2"><LoaderCircle className="animate-spin" size={17} />正在读取实验记录</span></div>}
          </div>
        </div>
      </section>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const succeeded = status === 'succeeded'
  const failed = status === 'failed'
  const Icon = succeeded ? CheckCircle2 : failed ? AlertCircle : Clock3
  return <span className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold ${succeeded ? 'bg-[#e8f7ef] text-success-dark' : failed ? 'bg-red-50 text-red-700' : 'bg-[#f0ecfe] text-brand-deep'}`}><Icon size={11} />{succeeded ? '已完成' : failed ? '失败' : '运行中'}</span>
}
