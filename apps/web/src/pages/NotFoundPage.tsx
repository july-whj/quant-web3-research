import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Brand } from '../components/Brand'

export function NotFoundPage() {
  return (
    <div className="surface-grid grid min-h-screen place-items-center p-5">
      <div className="max-w-lg text-center">
        <Brand />
        <p className="display-title mt-10 text-8xl text-brand">404</p>
        <h1 className="mt-5 text-2xl font-bold">这条研究路径还不存在</h1>
        <p className="mt-3 text-sm leading-6 text-muted">页面地址可能已经改变，或者功能仍在研究路线图中。</p>
        <Link className="button-primary mt-7" to="/"><ArrowLeft size={17} />返回首页</Link>
      </div>
    </div>
  )
}
