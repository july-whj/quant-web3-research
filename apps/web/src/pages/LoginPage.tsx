import { ArrowLeft, Database, FlaskConical, ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate } from 'react-router-dom'

import { Brand } from '../components/Brand'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import { WalletLoginButton } from '../features/auth/WalletLoginButton'
import { useSession } from '../features/auth/useSession'

export function LoginPage() {
  const { t } = useTranslation()
  const session = useSession()
  if (session.data) return <Navigate replace to="/app" />

  return (
    <div className="grid min-h-screen bg-white lg:grid-cols-[0.82fr_1.18fr]">
      <section className="relative hidden overflow-hidden bg-ink p-12 text-white lg:flex lg:flex-col">
        <Brand inverse />
        <div className="my-auto max-w-lg">
          <p className="eyebrow !text-white/50">{t('login.eyebrow')}</p>
          <h1 className="display-title mt-5 text-6xl">{t('login.title')}</h1>
          <p className="mt-6 text-base leading-8 text-white/58">{t('login.description')}</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-xs text-white/58">
          <span className="flex items-center gap-2"><Database size={14} className="text-[#a98cff]" />{t('login.dataVersion')}</span>
          <span className="flex items-center gap-2"><FlaskConical size={14} className="text-[#a98cff]" />{t('login.strategyExperiment')}</span>
          <span className="flex items-center gap-2"><ShieldCheck size={14} className="text-[#a98cff]" />{t('login.noAssetApproval')}</span>
        </div>
        <div className="absolute -bottom-36 -right-36 size-[430px] rounded-full border-[74px] border-white/[0.035]" />
      </section>

      <section className="surface-grid relative flex min-h-screen items-center justify-center p-5 sm:p-10">
        <div className="absolute right-6 top-6 hidden lg:block"><LanguageSwitcher /></div>
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center justify-between lg:hidden">
            <Brand />
            <LanguageSwitcher compact />
          </div>
          <Link className="mb-7 inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink" to="/"><ArrowLeft size={16} />{t('login.backHome')}</Link>
          <div className="research-card p-7 sm:p-9">
            <p className="eyebrow">{t('login.signIn')}</p>
            <h2 className="mt-3 text-3xl font-bold tracking-[-0.04em]">{t('login.cardTitle')}</h2>
            <p className="mt-3 text-sm leading-7 text-muted">{t('login.cardDescription')}</p>

            <div className="mt-7 [&>button]:w-full">
              <WalletLoginButton />
            </div>

            <div className="mt-7 space-y-3 border-t border-line pt-6 text-xs leading-5 text-muted">
              <p className="flex gap-2"><ShieldCheck className="mt-0.5 shrink-0 text-success" size={15} />{t('login.noGas')}</p>
              <p>{t('login.eoaOnly')}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
