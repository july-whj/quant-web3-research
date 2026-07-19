import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, Database, Download, Server, Waves } from 'lucide-react'

import { listDatasets } from '../features/datasets/api'

export function DataPage() {
  const datasets = useQuery({ queryKey: ['datasets'], queryFn: listDatasets })
  const sources = datasets.data?.length
    ? datasets.data.map((dataset) => ({
        exchange: dataset.exchange,
        symbol: dataset.symbol,
        timeframe: dataset.timeframe,
        records: String(dataset.row_count),
        status: 'ready',
      }))
    : [{ exchange: 'Binance', symbol: 'BTC/USDT', timeframe: '1d', records: '—', status: 'planned' }]
  return (
    <div className="animate-rise">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Data registry</p>
          <h1 className="mt-3 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">数据中心</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">先登记数据来源，再讨论策略表现。每个数据集都应留下交易所、交易对、周期和抓取范围。</p>
        </div>
        <button className="button-primary w-fit" type="button"><Download size={17} />获取新数据</button>
      </div>

      <section className="mt-8 research-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-7">
          <div><p className="font-bold">行情数据集</p><p className="mt-1 text-xs text-muted">本地 Parquet 文件与元数据索引</p></div>
          <span className="text-xs text-muted">{sources.length} 个来源</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="bg-[#fafafd] text-xs text-muted">
              <tr><th className="px-7 py-3 font-medium">交易所</th><th className="px-5 py-3 font-medium">交易对</th><th className="px-5 py-3 font-medium">周期</th><th className="px-5 py-3 font-medium">记录数</th><th className="px-7 py-3 text-right font-medium">状态</th></tr>
            </thead>
            <tbody className="divide-y divide-line">
              {sources.map((source) => (
                <tr key={`${source.exchange}-${source.timeframe}`}>
                  <td className="px-7 py-5 font-semibold">{source.exchange}</td><td className="px-5 py-5">{source.symbol}</td><td className="px-5 py-5 text-muted">{source.timeframe}</td><td className="px-5 py-5 text-muted">{source.records}</td>
                  <td className="px-7 py-5 text-right"><span className={`inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-semibold ${source.status === 'ready' ? 'bg-[#e8f7ef] text-success-dark' : 'bg-[#f2f2f5] text-muted'}`}>{source.status === 'ready' && <CheckCircle2 size={13} />}{source.status === 'ready' ? '可使用' : '待接入'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-3">
        {[
          { icon: Server, title: '交易所 API', text: '首版通过 CCXT 统一接入 Binance、OKX 等公开行情接口。' },
          { icon: Database, title: 'Parquet 文件', text: '大量 K 线保存在列式文件中，MySQL 只保存索引与研究元数据。' },
          { icon: Waves, title: '链上数据', text: '为后续版本预留节点、索引服务与链上指标的数据入口。' },
        ].map(({ icon: Icon, title, text }) => (
          <article className="research-card p-5" key={title}><Icon className="text-brand" size={22} /><h2 className="mt-5 font-bold">{title}</h2><p className="mt-2 text-sm leading-6 text-muted">{text}</p></article>
        ))}
      </section>
    </div>
  )
}
