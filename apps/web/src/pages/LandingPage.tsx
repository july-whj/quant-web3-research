import {
  ArrowRight,
  Beaker,
  BookOpen,
  Check,
  Database,
  GitBranch,
  Github,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Brand } from '../components/Brand'
import { EquityChart } from '../components/EquityChart'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import { WalletLoginButton } from '../features/auth/WalletLoginButton'

export function LandingPage() {
  const { t } = useTranslation()
  const capabilities = [
    { icon: Database, index: '01', title: t('landing.capabilityDataTitle'), text: t('landing.capabilityDataText') },
    { icon: GitBranch, index: '02', title: t('landing.capabilityStrategyTitle'), text: t('landing.capabilityStrategyText') },
    { icon: Beaker, index: '03', title: t('landing.capabilityEvidenceTitle'), text: t('landing.capabilityEvidenceText') },
  ]

  return (
    <div className="min-h-screen overflow-hidden bg-white">
      <header className="mx-auto flex h-20 max-w-[1240px] items-center justify-between px-5 sm:px-8">
        <span className="sm:hidden"><Brand compact /></span>
        <span className="hidden sm:inline"><Brand /></span>
        <nav className="hidden items-center gap-7 text-sm font-medium text-muted md:flex">
          <a className="hover:text-ink" href="#method">{t('landing.navMethod')}</a>
          <a className="hover:text-ink" href="#open-source">{t('landing.navOpenSource')}</a>
          <a className="inline-flex items-center gap-1.5 hover:text-ink" href="https://github.com/july-whj/quant-web3-research" rel="noreferrer" target="_blank"><Github size={15} />GitHub</a>
        </nav>
        <div className="flex items-center gap-2">
          <LanguageSwitcher compact />
          <WalletLoginButton compact />
        </div>
      </header>

      <main>
        <section className="surface-grid border-y border-line">
          <div className="mx-auto grid min-h-[680px] max-w-[1240px] items-center gap-14 px-5 py-16 sm:px-8 lg:grid-cols-[0.93fr_1.07fr] lg:py-24">
            <div className="animate-rise max-w-xl">
              <p className="eyebrow flex items-center gap-2"><Sparkles size={14} className="text-brand" />{t('landing.eyebrow')}</p>
              <h1 className="display-title mt-6 text-[clamp(3rem,6vw,5.4rem)]">
                <span className="block">{t('landing.heroLine1')}</span>
                <span className="block">{t('landing.heroLine2')}</span>
                <span className="block">{t('landing.heroLine3')}</span>
              </h1>
              <p className="mt-7 max-w-lg text-lg leading-8 text-muted">
                {t('landing.heroDescription')}
              </p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link className="button-primary" to="/login">{t('landing.start')} <ArrowRight size={17} /></Link>
                <a className="button-outline" href="#method"><BookOpen size={17} />{t('landing.viewMethod')}</a>
              </div>
              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted">
                <span className="flex items-center gap-2"><Check size={15} className="text-success" />{t('landing.noLiveTrading')}</span>
                <span className="flex items-center gap-2"><Check size={15} className="text-success" />{t('landing.traceable')}</span>
              </div>
            </div>

            <div className="animate-rise lg:pl-5" style={{ animationDelay: '120ms' }}>
              <div className="research-card relative overflow-hidden">
                <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-7">
                  <div>
                    <p className="text-sm font-semibold">MA20 / MA60 · BTC/USDT</p>
                    <p className="mt-1 text-xs text-muted">{t('landing.snapshotSubtitle')}</p>
                  </div>
                  <span className="rounded-lg bg-[#e8f7ef] px-2.5 py-1 text-xs font-semibold text-success-dark">{t('landing.reproduced')}</span>
                </div>
                <div className="grid grid-cols-3 border-b border-line">
                  {[
                    [t('landing.totalReturn'), '+17.9%'],
                    [t('landing.maxDrawdown'), '-8.4%'],
                    [t('landing.trades'), '14'],
                  ].map(([label, value], index) => (
                    <div className={`px-4 py-5 sm:px-6 ${index < 2 ? 'border-r border-line' : ''}`} key={label}>
                      <p className="text-xs text-muted">{label}</p>
                      <p className={`mt-2 text-xl font-bold tracking-[-0.03em] ${index === 0 ? 'text-success-dark' : ''}`}>{value}</p>
                    </div>
                  ))}
                </div>
                <div className="px-3 pb-2 pt-5 sm:px-6">
                  <div className="mb-2 flex items-center gap-4 px-2 text-xs text-muted">
                    <span className="flex items-center gap-2"><i className="block h-0.5 w-5 bg-brand" />{t('landing.strategyEquity')}</span>
                    <span className="flex items-center gap-2"><i className="block h-0.5 w-5 bg-[#b9bbc7]" />{t('landing.benchmark')}</span>
                  </div>
                  <EquityChart compact />
                </div>
                <div className="absolute -right-16 -top-16 size-40 rounded-full border-[28px] border-[rgba(113,50,245,0.06)]" />
              </div>
              <p className="mt-3 text-right text-xs text-silver">{t('landing.demoDisclaimer')}</p>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1240px] px-5 py-24 sm:px-8" id="method">
          <div className="max-w-2xl">
            <p className="eyebrow">{t('landing.loopEyebrow')}</p>
            <h2 className="display-title mt-4 text-4xl sm:text-5xl">{t('landing.loopTitle')}</h2>
            <p className="mt-5 text-lg leading-8 text-muted">{t('landing.loopDescription')}</p>
          </div>
          <div className="mt-12 grid border-y border-line md:grid-cols-3">
            {capabilities.map(({ icon: Icon, index, title, text }, itemIndex) => (
              <article className={`relative py-9 md:px-8 ${itemIndex > 0 ? 'border-t border-line md:border-l md:border-t-0' : ''}`} key={title}>
                <span className="absolute right-4 top-5 text-xs font-semibold text-silver">{index}</span>
                <Icon className="text-brand" size={25} />
                <h3 className="mt-7 text-xl font-bold">{title}</h3>
                <p className="mt-3 text-sm leading-7 text-muted">{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="bg-ink text-white" id="open-source">
          <div className="mx-auto grid max-w-[1240px] gap-12 px-5 py-20 sm:px-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-2xl">
              <ShieldCheck className="text-[#a98cff]" size={28} />
              <h2 className="display-title mt-6 text-4xl sm:text-5xl">{t('landing.openSourceTitle')}</h2>
              <p className="mt-5 text-base leading-8 text-white/62">{t('landing.openSourceDescription')}</p>
            </div>
            <Link className="button-primary w-fit" to="/login">{t('landing.enterWorkspace')} <ArrowRight size={17} /></Link>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-[1240px] flex-col gap-5 px-5 py-9 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <Brand />
        <p>{t('landing.footer')}</p>
      </footer>
    </div>
  )
}
