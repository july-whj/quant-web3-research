import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Beaker, Database, FlaskConical, Plus, TrendingDown, TrendingUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { EquityChart } from '../components/EquityChart'
import { useSession } from '../features/auth/useSession'
import { listBacktests } from '../features/backtests/api'
import { currentLanguage } from '../i18n'
import { formatDateTime, formatPercent, shortenAddress } from '../lib/format'

export function DashboardPage() {
  const { t } = useTranslation()
  const language = currentLanguage()
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
          <p className="eyebrow">{t('dashboard.eyebrow')}</p>
          <h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">{t('dashboard.title')}</h1>
          <p className="mt-3 text-sm text-muted">{t('dashboard.accountPrefix')} {session.data ? shortenAddress(session.data.address) : '—'} · {t('dashboard.historyOnly')}</p>
        </div>
        <Link className="button-primary w-fit" to="/app/backtests"><Plus size={17} />{t('dashboard.newBacktest')}</Link>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        {[
          { label: t('dashboard.savedBacktests'), value: String(runs.data?.length ?? 0), helper: t('dashboard.includingRunning'), icon: Beaker },
          { label: t('dashboard.latestReturn'), value: latestReturn === undefined ? '—' : formatPercent(latestReturn, language), helper: latest ? t('strategy.maCross') : t('dashboard.noCompleted'), icon: TrendingUp },
          { label: t('dashboard.latestDrawdown'), value: latestDrawdown === undefined ? '—' : formatPercent(latestDrawdown, language), helper: t('dashboard.drawdownHelper'), icon: TrendingDown },
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
              <p className="text-base font-bold">{t('dashboard.equitySnapshot')}</p>
              <p className="mt-1 text-xs text-muted">{t('dashboard.sampleCurve')}</p>
            </div>
            <span className="rounded-lg border border-line px-2.5 py-1 text-xs text-muted">BTC/USDT · 1d</span>
          </div>
          <div className="mt-5"><EquityChart /></div>
        </article>

        <article className="research-card p-5 sm:p-7">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-base font-bold">{t('dashboard.recentExperiments')}</p>
              <p className="mt-1 text-xs text-muted">{t('dashboard.sortByCreated')}</p>
            </div>
            <Link className="text-brand" to="/app/backtests" aria-label={t('dashboard.viewAll')}><ArrowRight size={18} /></Link>
          </div>
          <div className="mt-5 divide-y divide-line">
            {runs.data?.slice(0, 4).map((run) => (
              <div className="flex items-center justify-between gap-3 py-4" key={run.id}>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{t('strategy.maCross')}</p>
                  <p className="mt-1 text-xs text-muted">{formatDateTime(run.created_at, language)}</p>
                </div>
                <span className={`rounded-lg px-2 py-1 text-[11px] font-semibold ${run.status === 'succeeded' ? 'bg-[#e8f7ef] text-success-dark' : run.status === 'failed' ? 'bg-red-50 text-red-700' : 'bg-[#f0ecfe] text-brand-deep'}`}>{run.status === 'succeeded' ? t('common.succeeded') : run.status === 'failed' ? t('common.failed') : t('common.running')}</span>
              </div>
            ))}
            {!runs.isPending && !runs.data?.length && (
              <div className="py-10 text-center text-sm text-muted">{t('dashboard.noRecords')}</div>
            )}
          </div>
        </article>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-3">
        {[
          { to: '/app/data', title: t('dashboard.prepareData'), text: t('dashboard.prepareDataText'), icon: Database },
          { to: '/app/strategies', title: t('dashboard.understandRules'), text: t('dashboard.understandRulesText'), icon: FlaskConical },
          { to: '/app/backtests', title: t('dashboard.runCostBacktest'), text: t('dashboard.runCostBacktestText'), icon: Beaker },
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
