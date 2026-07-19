import { ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { Brand } from '../components/Brand'
import { LanguageSwitcher } from '../components/LanguageSwitcher'

export function NotFoundPage() {
  const { t } = useTranslation()
  return (
    <div className="surface-grid relative grid min-h-screen place-items-center p-5">
      <div className="absolute right-5 top-5 sm:right-8 sm:top-8"><LanguageSwitcher compact /></div>
      <div className="max-w-lg text-center">
        <Brand />
        <p className="display-title mt-10 text-8xl text-brand">404</p>
        <h1 className="mt-5 text-2xl font-bold">{t('notFound.title')}</h1>
        <p className="mt-3 text-sm leading-6 text-muted">{t('notFound.description')}</p>
        <Link className="button-primary mt-7" to="/"><ArrowLeft size={17} />{t('notFound.backHome')}</Link>
      </div>
    </div>
  )
}
