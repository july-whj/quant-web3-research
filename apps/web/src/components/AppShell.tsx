import {
  BarChart3,
  Beaker,
  BookOpenText,
  Database,
  FlaskConical,
  Menu,
  X,
} from 'lucide-react'
import { useState, type PropsWithChildren } from 'react'
import { NavLink } from 'react-router-dom'

import { WalletLoginButton } from '../features/auth/WalletLoginButton'
import { Brand } from './Brand'

const navigation = [
  { to: '/app', label: '研究概览', icon: BarChart3, end: true },
  { to: '/app/data', label: '数据中心', icon: Database },
  { to: '/app/strategies', label: '策略实验室', icon: FlaskConical },
  { to: '/app/backtests', label: '回测任务', icon: Beaker },
]

export function AppShell({ children }: PropsWithChildren) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const sidebar = (
    <div className="flex h-full flex-col bg-ink px-4 py-5 text-white">
      <div className="px-2"><Brand inverse /></div>
      <nav className="mt-10 grid gap-1.5" aria-label="研究工作区">
        {navigation.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                isActive ? 'bg-white text-ink' : 'text-white/64 hover:bg-white/8 hover:text-white'
              }`
            }
            end={end}
            key={to}
            onClick={() => setMobileOpen(false)}
            to={to}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-2xl border border-white/10 bg-white/[0.04] p-4">
        <BookOpenText size={18} className="text-[#a98cff]" />
        <p className="mt-3 text-sm font-semibold">研究，不是下注</p>
        <p className="mt-1 text-xs leading-5 text-white/52">默认只运行历史回测，不连接真实资金账户。</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-[#f8f8fb] lg:grid lg:grid-cols-[248px_1fr]">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] lg:block">{sidebar}</aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="关闭导航"
            className="absolute inset-0 bg-ink/35 backdrop-blur-[2px]"
            onClick={() => setMobileOpen(false)}
            type="button"
          />
          <aside className="relative h-full w-[280px]">
            <button
              aria-label="关闭导航"
              className="absolute right-4 top-5 z-10 grid size-9 place-items-center rounded-xl border border-white/15 text-white"
              onClick={() => setMobileOpen(false)}
              type="button"
            >
              <X size={18} />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <div className="lg:col-start-2">
        <header className="sticky top-0 z-30 flex min-h-[72px] items-center justify-between border-b border-line bg-white/92 px-5 backdrop-blur-xl sm:px-8">
          <div className="flex items-center gap-3">
            <button
              aria-label="打开导航"
              className="grid size-10 place-items-center rounded-xl border border-line lg:hidden"
              onClick={() => setMobileOpen(true)}
              type="button"
            >
              <Menu size={19} />
            </button>
            <div>
              <p className="text-sm font-semibold">Quant Web3 Research</p>
              <p className="hidden text-xs text-muted sm:block">可复现的 Web3 量化研究工作区</p>
            </div>
          </div>
          <WalletLoginButton compact />
        </header>
        <main className="mx-auto w-full max-w-[1440px] p-5 sm:p-8">{children}</main>
      </div>
    </div>
  )
}
