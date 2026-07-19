import { LoaderCircle } from 'lucide-react'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'

import { AppShell } from '../components/AppShell'
import { useSession } from '../features/auth/useSession'
import { BacktestPage } from '../pages/BacktestPage'
import { DashboardPage } from '../pages/DashboardPage'
import { DataPage } from '../pages/DataPage'
import { LandingPage } from '../pages/LandingPage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { StrategyPage } from '../pages/StrategyPage'

function RequireSession() {
  const session = useSession()

  if (session.isPending) {
    return (
      <div className="grid min-h-screen place-items-center bg-[#f8f8fb] text-muted">
        <span className="flex items-center gap-2"><LoaderCircle className="animate-spin" size={18} />正在恢复研究会话</span>
      </div>
    )
  }
  if (!session.data) return <Navigate replace to="/login" />
  return <Outlet />
}

function Workspace() {
  return <AppShell><Outlet /></AppShell>
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<LandingPage />} path="/" />
        <Route element={<LoginPage />} path="/login" />
        <Route element={<RequireSession />}>
          <Route element={<Workspace />}>
            <Route element={<DashboardPage />} path="/app" />
            <Route element={<DataPage />} path="/app/data" />
            <Route element={<StrategyPage />} path="/app/strategies" />
            <Route element={<BacktestPage />} path="/app/backtests" />
          </Route>
        </Route>
        <Route element={<NotFoundPage />} path="*" />
      </Routes>
    </BrowserRouter>
  )
}
