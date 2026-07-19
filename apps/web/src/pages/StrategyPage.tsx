import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Braces, Check, FlaskConical, GitCompareArrows } from 'lucide-react'
import { Link } from 'react-router-dom'

import { listStrategies } from '../features/backtests/api'

export function StrategyPage() {
  const strategies = useQuery({ queryKey: ['strategies'], queryFn: listStrategies })

  return (
    <div className="animate-rise">
      <p className="eyebrow">Strategy laboratory</p>
      <h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">策略实验室</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">策略不是一组神秘参数，而是一套可以明确写下、逐条验证的交易规则。</p>

      <section className="mt-8 grid gap-5 xl:grid-cols-[1fr_0.7fr]">
        <div className="research-card p-6 sm:p-8">
          <div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><GitCompareArrows size={21} /></span><div><p className="text-xs text-muted">首个内置策略</p><h2 className="text-xl font-bold">现货多头双均线</h2></div></div>
          <div className="mt-7 grid gap-3">
            {[
              ['入场', '短期均线向上穿过长期均线，在下一根 K 线开盘时持有现货。'],
              ['离场', '短期均线向下穿过长期均线，在下一根 K 线开盘时退出。'],
              ['约束', '不做空、不加杠杆，同一时刻只持有一个方向的仓位。'],
              ['成本', '每次成交扣除手续费，并允许设置固定滑点假设。'],
            ].map(([label, text]) => (
              <div className="grid gap-2 rounded-xl border border-line p-4 sm:grid-cols-[72px_1fr]" key={label}><span className="text-sm font-semibold text-brand-deep">{label}</span><p className="text-sm leading-6 text-muted">{text}</p></div>
            ))}
          </div>
          <Link className="button-primary mt-7 w-fit" to="/app/backtests">带着规则去回测 <ArrowRight size={17} /></Link>
        </div>

        <aside className="research-card p-6 sm:p-8">
          <div className="flex items-center gap-2"><Braces size={18} className="text-brand" /><h2 className="font-bold">参数定义</h2></div>
          <div className="mt-5 space-y-3">
            {(strategies.data?.[0]?.parameters ?? [
              { name: 'fast_window', label: '短期均线', type: 'integer' as const, default: 20, minimum: 2 },
              { name: 'slow_window', label: '长期均线', type: 'integer' as const, default: 60, minimum: 3 },
            ]).map((parameter) => (
              <div className="flex items-center justify-between rounded-xl bg-[#f8f8fb] px-4 py-3" key={parameter.name}><span><strong className="block text-sm">{parameter.label}</strong><span className="text-xs text-muted">{parameter.name}</span></span><code className="rounded-lg bg-white px-2 py-1 text-sm text-brand-deep">{parameter.default}</code></div>
            ))}
          </div>
          <div className="mt-6 border-t border-line pt-5">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">实验前检查</p>
            <ul className="mt-4 space-y-3 text-sm text-muted">
              {['短周期必须小于长周期', '信号只能使用当时已知数据', '收益必须扣除交易成本'].map((item) => <li className="flex gap-2" key={item}><Check className="mt-0.5 shrink-0 text-success" size={15} />{item}</li>)}
            </ul>
          </div>
        </aside>
      </section>

      <section className="mt-5 research-card flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-4"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><FlaskConical size={20} /></span><div><h2 className="font-bold">下一步：策略版本管理</h2><p className="mt-1 text-sm text-muted">将代码提交、数据版本和参数快照绑定到每一次回测。</p></div></div>
        <span className="w-fit rounded-lg border border-line px-2.5 py-1 text-xs text-muted">Roadmap · V0.2</span>
      </section>
    </div>
  )
}
