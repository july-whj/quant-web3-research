import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Beaker, Database, FlaskConical, Plus, TrendingDown, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'

import { EquityChart } from '../components/EquityChart'
import { useSession } from '../features/auth/useSession'
import { listBacktests } from '../features/backtests/api'
import { formatDateTime, formatPercent, shortenAddress } from '../lib/format'

export function DashboardPage() {
  const session = useSession()
  const runs = useQuery({ queryKey: ['backtests'], queryFn: listBacktests })
  const succeeded = runs.data?.filter((run) => run.status === 'succeeded') ?? []
  const latest = succeeded[0]
  const latestReturn = latest?.summary?.strategy_total_return
  const latestDrawdown = latest?.summary?.strategy_max_drawdown

  return (
    <div className="animate-rise">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Research overview</p>
          <h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">今天从哪个假设开始？</h1>
          <p className="mt-3 text-sm text-muted">研究账户 {session.data ? shortenAddress(session.data.address) : '—'} · 所有结果默认仅用于历史验证</p>
        </div>
        <Link className="button-primary w-fit" to="/app/backtests"><Plus size={17} />新建回测</Link>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        {[
          { label: '已保存回测', value: String(runs.data?.length ?? 0), helper: '含运行中任务', icon: Beaker },
          { label: '最近策略收益', value: latestReturn === undefined ? '—' : formatPercent(latestReturn), helper: latest ? latest.strategy_name : '暂无完成的实验', icon: TrendingUp },
          { label: '最近最大回撤', value: latestDrawdown === undefined ? '—' : formatPercent(latestDrawdown), helper: '回撤越小越稳定', icon: TrendingDown },
        ].map(({ label, value, helper, icon: Icon }) => (
          <article className="research-card p-5" key={label}>
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted">{label}</p>
              <span className="grid size-9 place-items-center rounded-xl bg-[rgba(113,50,245,0.08)] text-brand"><Icon size={17} /></span>
            </div>
            <p className="mt-5 text-3xl font-bold tracking-[-0.04em]">{value}</p>
            <p className="mt-2 text-xs text-silver">{helper}</p>
          </article>
        ))}
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[1.5fr_0.8fr]">
        <article className="research-card p-5 sm:p-7">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-base font-bold">策略净值快照</p>
              <p className="mt-1 text-xs text-muted">示例曲线 · 接入实际回测产物后自动替换</p>
            </div>
            <span className="rounded-lg border border-line px-2.5 py-1 text-xs text-muted">BTC/USDT · 1d</span>
          </div>
          <div className="mt-5"><EquityChart /></div>
        </article>

        <article className="research-card p-5 sm:p-7">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-base font-bold">最近实验</p>
              <p className="mt-1 text-xs text-muted">按创建时间排序</p>
            </div>
            <Link className="text-brand" to="/app/backtests" aria-label="查看全部回测"><ArrowRight size={18} /></Link>
          </div>
          <div className="mt-5 divide-y divide-line">
            {runs.data?.slice(0, 4).map((run) => (
              <div className="flex items-center justify-between gap-3 py-4" key={run.id}>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{run.strategy_name}</p>
                  <p className="mt-1 text-xs text-muted">{formatDateTime(run.created_at)}</p>
                </div>
                <span className={`rounded-lg px-2 py-1 text-[11px] font-semibold ${run.status === 'succeeded' ? 'bg-[#e8f7ef] text-success-dark' : run.status === 'failed' ? 'bg-red-50 text-red-700' : 'bg-[#f0ecfe] text-brand-deep'}`}>{run.status === 'succeeded' ? '已完成' : run.status === 'failed' ? '失败' : '运行中'}</span>
              </div>
            ))}
            {!runs.isPending && !runs.data?.length && (
              <div className="py-10 text-center text-sm text-muted">还没有回测记录</div>
            )}
          </div>
        </article>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-3">
        {[
          { to: '/app/data', title: '准备行情数据', text: '登记交易所、周期与数据版本', icon: Database },
          { to: '/app/strategies', title: '理解策略规则', text: '检查入场、离场与参数边界', icon: FlaskConical },
          { to: '/app/backtests', title: '运行成本回测', text: '同时比较策略与买入持有', icon: Beaker },
        ].map(({ to, title, text, icon: Icon }) => (
          <Link className="group research-card flex items-center gap-4 p-5 transition hover:-translate-y-0.5 hover:border-brand" key={to} to={to}>
            <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><Icon size={19} /></span>
            <span className="min-w-0"><strong className="block text-sm">{title}</strong><span className="mt-1 block truncate text-xs text-muted">{text}</span></span>
            <ArrowRight className="ml-auto shrink-0 text-silver transition group-hover:translate-x-1 group-hover:text-brand" size={17} />
          </Link>
        ))}
      </section>
    </div>
  )
}
