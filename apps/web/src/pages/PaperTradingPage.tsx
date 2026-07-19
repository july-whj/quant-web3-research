import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  Bot,
  CircleDollarSign,
  Clock3,
  Coins,
  Gauge,
  Layers3,
  LoaderCircle,
  Pause,
  Play,
  Plus,
  ReceiptText,
  RefreshCw,
  ShieldCheck,
  Square,
  WalletCards,
  X,
} from 'lucide-react'
import { useCallback, useMemo, useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { MarketChart, type ChartPriceLine } from '../features/market-chart/MarketChart'
import { getMarketChartPage } from '../features/market-chart/api'
import type { MarketChartSettings } from '../features/market-chart/types'
import {
  cancelPaperOrder,
  controlPaperBot,
  createPaperAccount,
  createPaperBot,
  createPaperOrder,
  depositPaperFunds,
  listPaperAccounts,
  listPaperBots,
  listPaperFills,
  listPaperLedger,
  listPaperOrders,
} from '../features/paper-trading/api'
import type {
  PaperAccount,
  PaperBot,
  PaperFill,
  PaperLedgerEntry,
  PaperOrder,
} from '../features/paper-trading/types'
import { currentLanguage, type AppLanguage } from '../i18n'
import { formatDateTime } from '../lib/format'


function money(value: string | number, language: AppLanguage, currency = 'USDT') {
  return `${new Intl.NumberFormat(language, { maximumFractionDigits: 2 }).format(Number(value))} ${currency}`
}

function quantity(value: string | number, language: AppLanguage) {
  return new Intl.NumberFormat(language, { maximumFractionDigits: 8 }).format(Number(value))
}

export function PaperTradingPage() {
  const { t } = useTranslation()
  const language = currentLanguage()
  const queryClient = useQueryClient()
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const accounts = useQuery({
    queryKey: ['paper', 'accounts'],
    queryFn: listPaperAccounts,
    refetchInterval: 5000,
  })
  const activeAccount = accounts.data?.find((item) => item.id === selectedAccountId)
    ?? accounts.data?.[0]
    ?? null
  const accountId = activeAccount?.id ?? ''
  const orders = useQuery({
    queryKey: ['paper', accountId, 'orders'],
    queryFn: () => listPaperOrders(accountId),
    enabled: Boolean(accountId),
    refetchInterval: 5000,
  })
  const fills = useQuery({
    queryKey: ['paper', accountId, 'fills'],
    queryFn: () => listPaperFills(accountId),
    enabled: Boolean(accountId),
    refetchInterval: 5000,
  })
  const ledger = useQuery({
    queryKey: ['paper', accountId, 'ledger'],
    queryFn: () => listPaperLedger(accountId),
    enabled: Boolean(accountId),
    refetchInterval: 5000,
  })
  const bots = useQuery({
    queryKey: ['paper', accountId, 'bots'],
    queryFn: () => listPaperBots(accountId),
    enabled: Boolean(accountId),
    refetchInterval: 5000,
  })
  const market = useQuery({
    queryKey: ['paper', 'market', activeAccount?.exchange],
    queryFn: () => getMarketChartPage({
      exchange: activeAccount?.exchange ?? 'binance',
      timeframe: '1m',
      fastWindow: 20,
      slowWindow: 60,
      includeSignals: false,
    }),
    enabled: Boolean(activeAccount),
    refetchInterval: 15_000,
  })

  const refreshPaper = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ['paper'] })
  }, [queryClient])
  const openOrders = (orders.data ?? []).filter((order) => order.status === 'open')
  const priceLines = useMemo<ChartPriceLine[]>(() => {
    const orderLines = openOrders
      .filter((order) => order.limit_price)
      .map((order) => ({
        id: order.id,
        price: Number(order.limit_price),
        color: order.side === 'buy' ? '#0f9d72' : '#e05d5d',
        title: `${order.side.toUpperCase()} ${quantity(order.quantity, language)}`,
        lineStyle: 'dashed' as const,
      }))
    const botLines = (bots.data ?? []).filter((bot) => bot.status === 'running').flatMap((bot) => [
      { id: `${bot.id}-lower`, price: Number(bot.lower_price), color: '#7132f5', title: 'GRID L', lineStyle: 'solid' as const },
      { id: `${bot.id}-upper`, price: Number(bot.upper_price), color: '#7132f5', title: 'GRID H', lineStyle: 'solid' as const },
    ])
    return [...orderLines, ...botLines]
  }, [bots.data, language, openOrders])
  const chartSettings = useMemo<MarketChartSettings>(() => ({
    volume: true,
    fastMa: false,
    slowMa: false,
    macd: false,
    signals: true,
    executions: false,
    fastWindow: 20,
    slowWindow: 60,
  }), [])
  const chartLabels = useMemo(() => ({
    open: t('data.open'), high: t('data.high'), low: t('data.low'), close: t('data.close'),
    volume: t('data.volume'), noCandles: t('data.noCandles'),
    buySignal: t('paper.buyFill'), sellSignal: t('paper.sellFill'),
    buyExecution: t('paper.buyFill'), sellExecution: t('paper.sellFill'),
  }), [t])
  const ignoreEarlier = useCallback(() => undefined, [])

  if (accounts.isPending) {
    return <div className="grid min-h-[520px] place-items-center text-sm text-muted"><LoaderCircle className="mr-2 animate-spin" size={18} />{t('paper.loading')}</div>
  }

  return (
    <div className="animate-rise">
      <header className="relative overflow-hidden rounded-2xl border border-[#252830] bg-[#111318] px-6 py-7 text-white shadow-[0_18px_60px_rgba(16,17,20,0.16)] sm:px-8">
        <div className="absolute right-0 top-0 h-full w-2/5 bg-[radial-gradient(circle_at_80%_20%,rgba(20,158,97,0.2),transparent_58%)]" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div><p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#9ca1ae]">{t('paper.eyebrow')}</p><h1 className="mt-3 text-3xl font-bold tracking-[-0.045em] sm:text-4xl">{t('paper.title')}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-[#b4b8c3]">{t('paper.description')}</p></div>
          <div className="flex items-center gap-3"><span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">PAPER FUNDS ONLY</span><button className="grid size-9 place-items-center rounded-xl border border-white/15 text-white/70 hover:bg-white/10 hover:text-white" onClick={refreshPaper} type="button"><RefreshCw size={15} /></button></div>
        </div>
      </header>

      <div className="mt-5 flex flex-col gap-3 rounded-2xl border border-line bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#eef8f3] text-success-dark"><WalletCards size={19} /></span>{activeAccount ? <label className="min-w-0"><span className="block text-[10px] font-bold uppercase tracking-[0.1em] text-muted">{t('paper.activeAccount')}</span><select className="mt-0.5 max-w-full bg-transparent text-sm font-bold outline-none" onChange={(event) => setSelectedAccountId(event.target.value)} value={activeAccount.id}>{accounts.data?.map((account) => <option key={account.id} value={account.id}>{account.name} · {account.exchange.toUpperCase()}</option>)}</select></label> : <div><strong className="text-sm">{t('paper.noAccount')}</strong><p className="text-xs text-muted">{t('paper.noAccountHint')}</p></div>}</div>
        <button className="button-outline min-h-10 px-3 py-2 text-sm" onClick={() => setShowCreate((value) => !value)} type="button">{showCreate ? <X size={15} /> : <Plus size={15} />}{showCreate ? t('common.close') : t('paper.createAccount')}</button>
      </div>

      {(showCreate || !activeAccount) && <AccountCreator onCreated={(account) => { setSelectedAccountId(account.id); setShowCreate(false); refreshPaper() }} />}

      {activeAccount && <>
        <AccountMetrics account={activeAccount} language={language} onDeposited={refreshPaper} />

        <section className="mt-5 grid min-w-0 gap-5 2xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="research-card min-w-0 overflow-hidden">
            <div className="flex items-center justify-between border-b border-line px-5 py-4"><div><p className="text-xs text-muted">{activeAccount.exchange.toUpperCase()} · BTC/USDT · 1m</p><h2 className="mt-1 text-sm font-bold">{t('paper.executionChart')}</h2></div><div className="text-right text-xs text-muted"><b className="block text-sm text-ink">{money(activeAccount.position.mark_price, language)}</b>{t('paper.latestMark')}</div></div>
            <MarketChart
              candles={market.data?.candles.items ?? []}
              hasMore={false}
              labels={chartLabels}
              loading={market.isPending}
              loadingEarlier={false}
              locale={language}
              onLoadEarlier={ignoreEarlier}
              priceLines={priceLines}
              settings={chartSettings}
              signals={(fills.data ?? []).map((fill) => ({ signal_time: fill.market_time, execution_time: fill.market_time, side: fill.side }))}
            />
            <div className="flex flex-wrap gap-x-5 gap-y-2 border-t border-line bg-[#fafafd] px-5 py-3 text-xs text-muted"><span><i className="mr-1 inline-block size-2 rounded-full bg-success" />{t('paper.buyOrderLine')}</span><span><i className="mr-1 inline-block size-2 rounded-full bg-[#e05d5d]" />{t('paper.sellOrderLine')}</span><span><i className="mr-1 inline-block size-2 rounded-full bg-brand" />{t('paper.gridBoundary')}</span></div>
          </div>
          <OrderTicket account={activeAccount} key={activeAccount.id} language={language} onCompleted={refreshPaper} />
        </section>

        <section className="mt-5 grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <TradingActivity
            account={activeAccount}
            fills={fills.data ?? []}
            language={language}
            ledger={ledger.data ?? []}
            onChanged={refreshPaper}
            orders={orders.data ?? []}
          />
          <GridBots account={activeAccount} bots={bots.data ?? []} key={activeAccount.id} language={language} onChanged={refreshPaper} />
        </section>
      </>}
    </div>
  )
}

function AccountCreator({ onCreated }: { onCreated: (account: PaperAccount) => void }) {
  const { t } = useTranslation()
  const [name, setName] = useState('BTC Paper #1')
  const [exchange, setExchange] = useState<'binance' | 'okx'>('binance')
  const [funds, setFunds] = useState(10_000)
  const mutation = useMutation({
    mutationFn: () => createPaperAccount({ name, exchange, initial_funds: funds, fee_rate: 0.001, slippage_rate: 0.0005, max_position_pct: 1, max_order_notional: 1_000_000 }),
    onSuccess: onCreated,
  })
  return <form className="research-card mt-5 grid gap-4 p-5 md:grid-cols-[1fr_180px_200px_auto] md:items-end" onSubmit={(event) => { event.preventDefault(); mutation.mutate() }}><label className="grid gap-1.5 text-xs font-semibold">{t('paper.accountName')}<input className="field-control" onChange={(event) => setName(event.target.value)} value={name} /></label><label className="grid gap-1.5 text-xs font-semibold">{t('data.exchange')}<select className="field-control" onChange={(event) => setExchange(event.target.value as 'binance' | 'okx')} value={exchange}><option value="binance">Binance</option><option value="okx">OKX</option></select></label><label className="grid gap-1.5 text-xs font-semibold">{t('paper.initialFunds')}<input className="field-control" min="100" onChange={(event) => setFunds(Number(event.target.value))} type="number" value={funds} /></label><button className="button-primary" disabled={mutation.isPending} type="submit">{mutation.isPending ? <LoaderCircle className="animate-spin" size={16} /> : <Plus size={16} />}{t('paper.create')}</button>{mutation.error && <p className="text-xs text-red-700 md:col-span-4">{mutation.error.message}</p>}</form>
}

function AccountMetrics({ account, language, onDeposited }: { account: PaperAccount; language: AppLanguage; onDeposited: () => void }) {
  const { t } = useTranslation()
  const [amount, setAmount] = useState(1000)
  const [open, setOpen] = useState(false)
  const deposit = useMutation({ mutationFn: () => depositPaperFunds(account.id, amount), onSuccess: () => { setOpen(false); onDeposited() } })
  const quote = account.balances.find((item) => item.asset === 'USDT')
  const base = account.balances.find((item) => item.asset === 'BTC')
  const metrics = [
    [t('paper.totalEquity'), money(account.equity, language), CircleDollarSign],
    [t('paper.availableUsdt'), money(quote?.available ?? 0, language), WalletCards],
    [t('paper.btcPosition'), `${quantity(Number(base?.available ?? 0) + Number(base?.locked ?? 0), language)} BTC`, Coins],
    [t('paper.unrealizedPnl'), money(account.position.unrealized_pnl, language), Gauge],
    [t('paper.totalFees'), money(account.total_fees, language), ReceiptText],
    [t('paper.gasCost'), money(account.total_gas, language), ShieldCheck],
  ] as const
  return <><section className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">{metrics.map(([label, value, Icon]) => <div className="research-card p-4" key={label}><span className="flex items-center justify-between text-xs text-muted">{label}<Icon size={14} /></span><strong className="mt-2 block break-words text-base">{value}</strong></div>)}</section><div className="mt-3 flex justify-end">{open ? <form className="flex items-center gap-2" onSubmit={(event) => { event.preventDefault(); deposit.mutate() }}><input className="field-control w-40 py-2" min="1" onChange={(event) => setAmount(Number(event.target.value))} type="number" value={amount} /><button className="button-primary min-h-10 px-3 py-2 text-sm" type="submit">{t('paper.confirmFunds')}</button><button className="grid size-9 place-items-center rounded-lg border border-line" onClick={() => setOpen(false)} type="button"><X size={14} /></button></form> : <button className="text-xs font-semibold text-brand hover:text-brand-deep" onClick={() => setOpen(true)} type="button">+ {t('paper.addFunds')}</button>}</div></>
}

function OrderTicket({ account, language, onCompleted }: { account: PaperAccount; language: AppLanguage; onCompleted: () => void }) {
  const { t } = useTranslation()
  const [side, setSide] = useState<'buy' | 'sell'>('buy')
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market')
  const [quantityValue, setQuantity] = useState(0.001)
  const [limitPrice, setLimitPrice] = useState(Number(account.position.mark_price))
  const mutation = useMutation({
    mutationFn: () => createPaperOrder(account.id, { side, order_type: orderType, quantity: quantityValue, ...(orderType === 'limit' ? { limit_price: limitPrice } : {}) }),
    onSuccess: onCompleted,
  })
  const reference = orderType === 'limit' ? limitPrice : Number(account.position.mark_price)
  const slip = orderType === 'market' ? Number(account.slippage_rate) : 0
  const execution = reference * (1 + (side === 'buy' ? slip : -slip))
  const notional = execution * quantityValue
  const fee = notional * Number(account.fee_rate)
  return <form className="research-card h-fit overflow-hidden" onSubmit={(event: FormEvent) => { event.preventDefault(); mutation.mutate() }}><div className="border-b border-line bg-[#fafafd] px-5 py-4"><div className="flex items-center gap-2"><Coins className="text-brand" size={17} /><h2 className="text-sm font-bold">{t('paper.manualOrder')}</h2></div></div><div className="space-y-5 p-5"><div className="grid grid-cols-2 rounded-xl bg-[#f1f1f4] p-1">{(['buy', 'sell'] as const).map((value) => <button className={`rounded-lg py-2.5 text-sm font-bold ${side === value ? value === 'buy' ? 'bg-success text-white shadow-sm' : 'bg-[#d95353] text-white shadow-sm' : 'text-muted'}`} key={value} onClick={() => setSide(value)} type="button">{t(`paper.${value}`)}</button>)}</div><div className="grid grid-cols-2 gap-2">{(['market', 'limit'] as const).map((value) => <button className={`rounded-lg border px-3 py-2 text-xs font-semibold ${orderType === value ? 'border-brand bg-[#f4f0ff] text-brand-deep' : 'border-line text-muted'}`} key={value} onClick={() => setOrderType(value)} type="button">{t(`paper.${value}`)}</button>)}</div><label className="grid gap-1.5 text-xs font-semibold">{t('paper.quantity')}<div className="relative"><input className="field-control pr-14" min="0.00000001" onChange={(event) => setQuantity(Number(event.target.value))} step="0.0001" type="number" value={quantityValue} /><span className="absolute right-3 top-3 text-xs text-muted">BTC</span></div></label>{orderType === 'limit' && <label className="grid gap-1.5 text-xs font-semibold">{t('paper.limitPrice')}<div className="relative"><input className="field-control pr-16" min="1" onChange={(event) => setLimitPrice(Number(event.target.value))} type="number" value={limitPrice} /><span className="absolute right-3 top-3 text-xs text-muted">USDT</span></div></label>}<div className="space-y-2 rounded-xl border border-line bg-[#fafafd] p-4 text-xs"><EstimateRow label={t('paper.estimatedPrice')} value={money(execution, language)} /><EstimateRow label={t('paper.notional')} value={money(notional, language)} /><EstimateRow label={t('paper.estimatedFee')} value={money(fee, language)} /><EstimateRow label={t('paper.estimatedSlippage')} value={money(Math.abs(execution - reference) * quantityValue, language)} /><EstimateRow label={t('paper.estimatedGas')} value={`0 USDT · ${t('paper.cexNoGas')}`} /></div>{mutation.error && <p className="flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700"><AlertCircle className="shrink-0" size={15} />{mutation.error.message}</p>}<button className={`flex min-h-12 w-full items-center justify-center gap-2 rounded-xl font-bold text-white ${side === 'buy' ? 'bg-success hover:bg-success-dark' : 'bg-[#d95353] hover:bg-[#ba4141]'}`} disabled={mutation.isPending || quantityValue <= 0 || reference <= 0} type="submit">{mutation.isPending ? <LoaderCircle className="animate-spin" size={17} /> : <Play size={17} />}{side === 'buy' ? t('paper.submitBuy') : t('paper.submitSell')}</button><p className="text-center text-[10px] leading-4 text-muted">{t('paper.simulationOnly')}</p></div></form>
}

function EstimateRow({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between gap-3"><span className="text-muted">{label}</span><strong className="text-right font-medium text-ink">{value}</strong></div>
}

function TradingActivity({ account, fills, language, ledger, onChanged, orders }: { account: PaperAccount; fills: PaperFill[]; language: AppLanguage; ledger: PaperLedgerEntry[]; onChanged: () => void; orders: PaperOrder[] }) {
  const { t } = useTranslation()
  const [tab, setTab] = useState<'orders' | 'fills' | 'ledger'>('orders')
  const cancel = useMutation({ mutationFn: (orderId: string) => cancelPaperOrder(account.id, orderId), onSuccess: onChanged })
  return <div className="research-card overflow-hidden"><div className="flex items-center justify-between border-b border-line px-5 py-4"><div className="flex items-center gap-2"><Clock3 className="text-brand" size={17} /><h2 className="text-sm font-bold">{t('paper.activity')}</h2></div><div className="flex rounded-lg bg-[#f1f1f4] p-1">{(['orders', 'fills', 'ledger'] as const).map((value) => <button className={`rounded-md px-3 py-1.5 text-[11px] font-semibold ${tab === value ? 'bg-white text-ink shadow-sm' : 'text-muted'}`} key={value} onClick={() => setTab(value)} type="button">{t(`paper.${value}`)}</button>)}</div></div><div className="max-h-[440px] overflow-auto">{tab === 'orders' && <OrdersTable language={language} onCancel={(id) => cancel.mutate(id)} orders={orders} />}{tab === 'fills' && <FillsTable fills={fills} language={language} />}{tab === 'ledger' && <LedgerTable language={language} ledger={ledger} />}</div></div>
}

function OrdersTable({ language, onCancel, orders }: { language: AppLanguage; onCancel: (id: string) => void; orders: PaperOrder[] }) {
  const { t } = useTranslation()
  if (!orders.length) return <EmptyState text={t('paper.noOrders')} />
  return <div className="divide-y divide-line">{orders.map((order) => <div className="grid gap-3 px-5 py-4 sm:grid-cols-[1fr_0.8fr_0.7fr_auto] sm:items-center" key={order.id}><div><div className="flex items-center gap-2"><strong className={order.side === 'buy' ? 'text-success-dark' : 'text-[#b64545]'}>{t(`paper.${order.side}`)}</strong><StatusPill status={order.status} /><span className="text-[10px] uppercase text-muted">{order.order_type}</span></div><p className="mt-1 text-xs text-muted">{formatDateTime(order.created_at, language)} · {order.bot_id ? 'GRID' : 'MANUAL'}</p></div><span className="text-xs"><small className="block text-muted">{t('paper.quantity')}</small>{quantity(order.quantity, language)} BTC</span><span className="text-xs"><small className="block text-muted">{t('paper.price')}</small>{order.average_price || order.limit_price ? money(order.average_price ?? order.limit_price ?? 0, language) : 'MARKET'}</span>{order.status === 'open' ? <button className="rounded-lg border border-line px-2.5 py-1.5 text-xs font-semibold text-muted hover:border-red-300 hover:text-red-700" onClick={() => onCancel(order.id)} type="button">{t('paper.cancel')}</button> : <code className="text-[10px] text-silver">{order.id.slice(0, 7)}</code>}</div>)}</div>
}

function FillsTable({ fills, language }: { fills: PaperFill[]; language: AppLanguage }) {
  const { t } = useTranslation()
  if (!fills.length) return <EmptyState text={t('paper.noFills')} />
  return <div className="divide-y divide-line">{fills.map((fill) => <div className="grid gap-3 px-5 py-4 sm:grid-cols-[1fr_0.8fr_0.8fr]" key={fill.id}><div><strong className={fill.side === 'buy' ? 'text-success-dark' : 'text-[#b64545]'}>{t(`paper.${fill.side}Fill`)}</strong><p className="mt-1 text-xs text-muted">{formatDateTime(fill.market_time, language)}</p></div><span className="text-xs"><small className="block text-muted">{t('paper.executionPrice')}</small>{money(fill.execution_price, language)}<small className="mt-1 block text-muted">{quantity(fill.quantity, language)} BTC</small></span><span className="text-xs"><small className="block text-muted">{t('paper.cost')}</small>{money(Number(fill.fee_amount) + Number(fill.slippage_amount), language)}<small className="mt-1 block text-muted">Fee + Slippage</small></span></div>)}</div>
}

function LedgerTable({ language, ledger }: { language: AppLanguage; ledger: PaperLedgerEntry[] }) {
  const { t } = useTranslation()
  if (!ledger.length) return <EmptyState text={t('paper.noLedger')} />
  return <div className="divide-y divide-line">{ledger.map((entry) => <div className="grid grid-cols-[1fr_auto] gap-3 px-5 py-3" key={entry.id}><div><strong className="text-xs">{t(`paper.ledgerTypes.${entry.entry_type}`, { defaultValue: entry.entry_type })}</strong><p className="mt-1 text-[11px] text-muted">{formatDateTime(entry.created_at, language)} · {entry.asset}</p></div><strong className={`text-sm ${Number(entry.amount) >= 0 ? 'text-success-dark' : 'text-[#b64545]'}`}>{Number(entry.amount) >= 0 ? '+' : ''}{quantity(entry.amount, language)}</strong></div>)}</div>
}

function GridBots({ account, bots, language, onChanged }: { account: PaperAccount; bots: PaperBot[]; language: AppLanguage; onChanged: () => void }) {
  const { t } = useTranslation()
  const mark = Number(account.position.mark_price)
  const [name, setName] = useState('BTC Grid #1')
  const [lower, setLower] = useState(Math.round(mark * 0.9))
  const [upper, setUpper] = useState(Math.round(mark * 1.1))
  const [count, setCount] = useState(8)
  const [investment, setInvestment] = useState(2000)
  const create = useMutation({ mutationFn: () => createPaperBot(account.id, { name, lower_price: lower, upper_price: upper, grid_count: count, grid_mode: 'arithmetic', investment }), onSuccess: onChanged })
  const control = useMutation({ mutationFn: ({ botId, action }: { botId: string; action: 'start' | 'pause' | 'stop' }) => controlPaperBot(account.id, botId, action), onSuccess: onChanged })
  return <div className="research-card overflow-hidden"><div className="border-b border-line bg-[#fafafd] px-5 py-4"><div className="flex items-center gap-2"><Bot className="text-brand" size={17} /><h2 className="text-sm font-bold">{t('paper.gridBots')}</h2></div><p className="mt-1 text-xs text-muted">{t('paper.gridHint')}</p></div><form className="grid gap-3 border-b border-line p-5" onSubmit={(event) => { event.preventDefault(); create.mutate() }}><label className="grid gap-1 text-xs font-semibold">{t('paper.botName')}<input className="field-control py-2.5" onChange={(event) => setName(event.target.value)} value={name} /></label><div className="grid grid-cols-2 gap-3"><label className="grid gap-1 text-xs font-semibold">{t('paper.lower')}<input className="field-control py-2.5" onChange={(event) => setLower(Number(event.target.value))} type="number" value={lower} /></label><label className="grid gap-1 text-xs font-semibold">{t('paper.upper')}<input className="field-control py-2.5" onChange={(event) => setUpper(Number(event.target.value))} type="number" value={upper} /></label></div><button className="text-left text-[11px] font-semibold text-brand" onClick={() => { setLower(Math.round(mark * 0.9)); setUpper(Math.round(mark * 1.1)) }} type="button">{t('paper.useMarketRange')}</button><div className="grid grid-cols-2 gap-3"><label className="grid gap-1 text-xs font-semibold">{t('paper.gridCount')}<input className="field-control py-2.5" max="50" min="2" onChange={(event) => setCount(Number(event.target.value))} type="number" value={count} /></label><label className="grid gap-1 text-xs font-semibold">{t('paper.investment')}<input className="field-control py-2.5" min="1" onChange={(event) => setInvestment(Number(event.target.value))} type="number" value={investment} /></label></div>{create.error && <p className="text-xs text-red-700">{create.error.message}</p>}<button className="button-outline min-h-10 py-2 text-sm" type="submit"><Layers3 size={15} />{t('paper.createGrid')}</button></form><div className="max-h-[360px] divide-y divide-line overflow-auto">{bots.map((bot) => <div className="p-5" key={bot.id}><div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-2"><strong className="text-sm">{bot.name}</strong><StatusPill status={bot.status} /></div><p className="mt-1 text-xs text-muted">{money(bot.lower_price, language)} — {money(bot.upper_price, language)} · {bot.grid_count} grids</p></div><strong className="text-xs text-success-dark">{money(bot.realized_profit, language)}</strong></div><div className="mt-4 flex gap-2">{(bot.status === 'draft' || bot.status === 'paused') && <button className="rounded-lg bg-ink px-3 py-1.5 text-xs font-semibold text-white" onClick={() => control.mutate({ botId: bot.id, action: 'start' })} type="button"><Play className="mr-1 inline" size={12} />{bot.status === 'paused' ? t('paper.resume') : t('paper.start')}</button>}{bot.status === 'running' && <button className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold" onClick={() => control.mutate({ botId: bot.id, action: 'pause' })} type="button"><Pause className="mr-1 inline" size={12} />{t('paper.pause')}</button>}{['running', 'paused', 'error'].includes(bot.status) && <button className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-red-700" onClick={() => control.mutate({ botId: bot.id, action: 'stop' })} type="button"><Square className="mr-1 inline" size={11} />{t('paper.stop')}</button>}</div></div>)}{!bots.length && <EmptyState text={t('paper.noBots')} />}</div></div>
}

function StatusPill({ status }: { status: string }) {
  const { t } = useTranslation()
  const tone = status === 'filled' || status === 'running' ? 'bg-emerald-50 text-success-dark' : status === 'cancelled' || status === 'stopped' ? 'bg-[#f1f1f4] text-muted' : status === 'error' || status === 'rejected' ? 'bg-red-50 text-red-700' : 'bg-[#f0ecfe] text-brand-deep'
  return <span className={`rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase ${tone}`}>{t(`paper.status.${status}`, { defaultValue: status })}</span>
}

function EmptyState({ text }: { text: string }) {
  return <div className="grid min-h-28 place-items-center px-5 text-center text-xs text-muted">{text}</div>
}
