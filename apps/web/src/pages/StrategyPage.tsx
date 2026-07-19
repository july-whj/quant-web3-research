import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Braces, Check, FlaskConical, GitCompareArrows } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { listStrategies } from '../features/backtests/api'

export function StrategyPage() {
  const { t } = useTranslation()
  const strategies = useQuery({ queryKey: ['strategies'], queryFn: listStrategies })
  const parameterLabels: Record<string, string> = {
    fast_window: t('strategy.fastWindow'),
    slow_window: t('strategy.slowWindow'),
    fee_rate: t('strategy.feeRate'),
    slippage_rate: t('strategy.slippageRate'),
  }

  return (
    <div className="animate-rise">
      <p className="eyebrow">{t('strategy.eyebrow')}</p>
      <h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">{t('strategy.title')}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{t('strategy.description')}</p>

      <section className="mt-8 grid gap-5 xl:grid-cols-[1fr_0.7fr]">
        <div className="research-card p-6 sm:p-8">
          <div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><GitCompareArrows size={21} /></span><div><p className="text-xs text-muted">{t('strategy.firstBuiltIn')}</p><h2 className="text-xl font-bold">{t('strategy.maCross')}</h2></div></div>
          <div className="mt-7 grid gap-3">
            {[
              [t('strategy.entry'), t('strategy.entryText')],
              [t('strategy.exit'), t('strategy.exitText')],
              [t('strategy.constraints'), t('strategy.constraintsText')],
              [t('strategy.costs'), t('strategy.costsText')],
            ].map(([label, text]) => (
              <div className="grid gap-2 rounded-xl border border-line p-4 sm:grid-cols-[72px_1fr]" key={label}><span className="text-sm font-semibold text-brand-deep">{label}</span><p className="text-sm leading-6 text-muted">{text}</p></div>
            ))}
          </div>
          <Link className="button-primary mt-7 w-fit" to="/app/backtests">{t('strategy.runBacktest')} <ArrowRight size={17} /></Link>
        </div>

        <aside className="research-card p-6 sm:p-8">
          <div className="flex items-center gap-2"><Braces size={18} className="text-brand" /><h2 className="font-bold">{t('strategy.parameters')}</h2></div>
          <div className="mt-5 space-y-3">
            {(strategies.data?.[0]?.parameters ?? [
              { name: 'fast_window', label: t('strategy.fastWindow'), type: 'integer' as const, default: 20, minimum: 2 },
              { name: 'slow_window', label: t('strategy.slowWindow'), type: 'integer' as const, default: 60, minimum: 3 },
            ]).map((parameter) => (
              <div className="flex items-center justify-between rounded-xl bg-[#f8f8fb] px-4 py-3" key={parameter.name}><span><strong className="block text-sm">{parameterLabels[parameter.name] ?? parameter.label}</strong><span className="text-xs text-muted">{parameter.name}</span></span><code className="rounded-lg bg-white px-2 py-1 text-sm text-brand-deep">{parameter.default}</code></div>
            ))}
          </div>
          <div className="mt-6 border-t border-line pt-5">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">{t('strategy.checklist')}</p>
            <ul className="mt-4 space-y-3 text-sm text-muted">
              {[t('strategy.checkWindows'), t('strategy.checkKnownData'), t('strategy.checkCosts')].map((item) => <li className="flex gap-2" key={item}><Check className="mt-0.5 shrink-0 text-success" size={15} />{item}</li>)}
            </ul>
          </div>
        </aside>
      </section>

      <section className="mt-5 research-card flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-4"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#f0ecfe] text-brand"><FlaskConical size={20} /></span><div><h2 className="font-bold">{t('strategy.next')}</h2><p className="mt-1 text-sm text-muted">{t('strategy.nextText')}</p></div></div>
        <span className="w-fit rounded-lg border border-line px-2.5 py-1 text-xs text-muted">Roadmap · V0.2</span>
      </section>
    </div>
  )
}
