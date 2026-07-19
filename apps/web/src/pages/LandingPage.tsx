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

import { Brand } from '../components/Brand'
import { EquityChart } from '../components/EquityChart'
import { WalletLoginButton } from '../features/auth/WalletLoginButton'

const capabilities = [
  {
    icon: Database,
    index: '01',
    title: '数据有出处',
    text: '记录交易所、交易对、周期与抓取时间，让每一次研究都能回到原始证据。',
  },
  {
    icon: GitBranch,
    index: '02',
    title: '策略有版本',
    text: '参数、成本假设与代码版本共同保存，避免“这次结果到底怎么跑出来的”。',
  },
  {
    icon: Beaker,
    index: '03',
    title: '结论可复现',
    text: '收益、回撤、手续费和基准同时呈现，把漂亮曲线拆成可验证的研究结论。',
  },
]

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden bg-white">
      <header className="mx-auto flex h-20 max-w-[1240px] items-center justify-between px-5 sm:px-8">
        <Brand />
        <nav className="hidden items-center gap-7 text-sm font-medium text-muted md:flex">
          <a className="hover:text-ink" href="#method">研究方法</a>
          <a className="hover:text-ink" href="#open-source">开源原则</a>
          <a className="inline-flex items-center gap-1.5 hover:text-ink" href="https://github.com" rel="noreferrer" target="_blank"><Github size={15} />GitHub</a>
        </nav>
        <WalletLoginButton compact />
      </header>

      <main>
        <section className="surface-grid border-y border-line">
          <div className="mx-auto grid min-h-[680px] max-w-[1240px] items-center gap-14 px-5 py-16 sm:px-8 lg:grid-cols-[0.93fr_1.07fr] lg:py-24">
            <div className="animate-rise max-w-xl">
              <p className="eyebrow flex items-center gap-2"><Sparkles size={14} className="text-brand" />Open-source research system</p>
              <h1 className="display-title mt-6 text-[clamp(3.1rem,6.6vw,5.8rem)]">
                把策略判断，<br />变成研究<span className="hidden lg:block">证据。</span><span className="lg:hidden">证据。</span>
              </h1>
              <p className="mt-7 max-w-lg text-lg leading-8 text-muted">
                从 BTC 行情、策略参数到手续费与回撤，完整保存研究过程。目标不是预测下一根 K 线，而是让每一个结论都能被复查。
              </p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link className="button-primary" to="/login">开始研究 <ArrowRight size={17} /></Link>
                <a className="button-outline" href="#method"><BookOpen size={17} />查看方法</a>
              </div>
              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted">
                <span className="flex items-center gap-2"><Check size={15} className="text-success" />默认不连接实盘</span>
                <span className="flex items-center gap-2"><Check size={15} className="text-success" />代码与实验可追溯</span>
              </div>
            </div>

            <div className="animate-rise lg:pl-5" style={{ animationDelay: '120ms' }}>
              <div className="research-card relative overflow-hidden">
                <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-7">
                  <div>
                    <p className="text-sm font-semibold">MA20 / MA60 · BTC/USDT</p>
                    <p className="mt-1 text-xs text-muted">研究快照 · 365 日 · 含交易成本</p>
                  </div>
                  <span className="rounded-lg bg-[#e8f7ef] px-2.5 py-1 text-xs font-semibold text-success-dark">已复现</span>
                </div>
                <div className="grid grid-cols-3 border-b border-line">
                  {[
                    ['累计收益', '+17.9%'],
                    ['最大回撤', '-8.4%'],
                    ['交易次数', '14'],
                  ].map(([label, value], index) => (
                    <div className={`px-4 py-5 sm:px-6 ${index < 2 ? 'border-r border-line' : ''}`} key={label}>
                      <p className="text-xs text-muted">{label}</p>
                      <p className={`mt-2 text-xl font-bold tracking-[-0.03em] ${index === 0 ? 'text-success-dark' : ''}`}>{value}</p>
                    </div>
                  ))}
                </div>
                <div className="px-3 pb-2 pt-5 sm:px-6">
                  <div className="mb-2 flex items-center gap-4 px-2 text-xs text-muted">
                    <span className="flex items-center gap-2"><i className="block h-0.5 w-5 bg-brand" />策略净值</span>
                    <span className="flex items-center gap-2"><i className="block h-0.5 w-5 bg-[#b9bbc7]" />买入持有</span>
                  </div>
                  <EquityChart compact />
                </div>
                <div className="absolute -right-16 -top-16 size-40 rounded-full border-[28px] border-[rgba(113,50,245,0.06)]" />
              </div>
              <p className="mt-3 text-right text-xs text-silver">演示数据，仅用于界面说明，不构成投资建议</p>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1240px] px-5 py-24 sm:px-8" id="method">
          <div className="max-w-2xl">
            <p className="eyebrow">Research loop</p>
            <h2 className="display-title mt-4 text-4xl sm:text-5xl">一套能反复运行的研究流程</h2>
            <p className="mt-5 text-lg leading-8 text-muted">系统把书里的方法变成工具，也把工具中的真实问题继续写回书中。</p>
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
              <h2 className="display-title mt-6 text-4xl sm:text-5xl">开放代码，也开放失败过程</h2>
              <p className="mt-5 text-base leading-8 text-white/62">策略参数、回测假设和实验记录都进入版本管理。系统不承诺盈利，只帮助研究者更早发现错误。</p>
            </div>
            <Link className="button-primary w-fit" to="/login">进入工作区 <ArrowRight size={17} /></Link>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-[1240px] flex-col gap-5 px-5 py-9 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <Brand />
        <p>Open-source · Research first · No financial advice</p>
      </footer>
    </div>
  )
}
