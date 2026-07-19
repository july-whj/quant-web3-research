import { ArrowLeft, Database, FlaskConical, ShieldCheck } from 'lucide-react'
import { Link, Navigate } from 'react-router-dom'

import { Brand } from '../components/Brand'
import { WalletLoginButton } from '../features/auth/WalletLoginButton'
import { useSession } from '../features/auth/useSession'

export function LoginPage() {
  const session = useSession()
  if (session.data) return <Navigate replace to="/app" />

  return (
    <div className="grid min-h-screen bg-white lg:grid-cols-[0.82fr_1.18fr]">
      <section className="relative hidden overflow-hidden bg-ink p-12 text-white lg:flex lg:flex-col">
        <Brand inverse />
        <div className="my-auto max-w-lg">
          <p className="eyebrow !text-white/50">Research identity</p>
          <h1 className="display-title mt-5 text-6xl">一个钱包，保存整条研究轨迹。</h1>
          <p className="mt-6 text-base leading-8 text-white/58">无需密码。通过一次性消息签名确认身份，把数据集、策略版本和回测记录关联到同一个研究账户。</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-xs text-white/58">
          <span className="flex items-center gap-2"><Database size={14} className="text-[#a98cff]" />数据版本</span>
          <span className="flex items-center gap-2"><FlaskConical size={14} className="text-[#a98cff]" />策略实验</span>
          <span className="flex items-center gap-2"><ShieldCheck size={14} className="text-[#a98cff]" />无资产授权</span>
        </div>
        <div className="absolute -bottom-36 -right-36 size-[430px] rounded-full border-[74px] border-white/[0.035]" />
      </section>

      <section className="surface-grid flex min-h-screen items-center justify-center p-5 sm:p-10">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center justify-between lg:hidden">
            <Brand />
          </div>
          <Link className="mb-7 inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink" to="/"><ArrowLeft size={16} />返回首页</Link>
          <div className="research-card p-7 sm:p-9">
            <p className="eyebrow">Sign in</p>
            <h2 className="mt-3 text-3xl font-bold tracking-[-0.04em]">进入研究工作区</h2>
            <p className="mt-3 text-sm leading-7 text-muted">连接支持 BNB Smart Chain 的 EVM 钱包，并签署由服务端生成的一次性登录消息。</p>

            <div className="mt-7 [&>button]:w-full">
              <WalletLoginButton />
            </div>

            <div className="mt-7 space-y-3 border-t border-line pt-6 text-xs leading-5 text-muted">
              <p className="flex gap-2"><ShieldCheck className="mt-0.5 shrink-0 text-success" size={15} />签名不消耗 Gas，不会创建交易，也不授予转账权限。</p>
              <p>当前版本只支持外部账户钱包（EOA）；智能合约钱包将在后续版本加入。</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
