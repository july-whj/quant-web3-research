import { ChevronDown, Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { currentLanguage, type AppLanguage } from '../i18n'

const languages: Array<{ code: AppLanguage; label: string; shortLabel: string }> = [
  { code: 'zh-CN', label: '简体中文', shortLabel: '简' },
  { code: 'zh-TW', label: '繁體中文', shortLabel: '繁' },
  { code: 'ja', label: '日本語', shortLabel: '日' },
  { code: 'en', label: 'English', shortLabel: 'EN' },
]

interface LanguageSwitcherProps {
  compact?: boolean
  inverse?: boolean
}

export function LanguageSwitcher({ compact = false, inverse = false }: LanguageSwitcherProps) {
  const { t, i18n } = useTranslation()

  return (
    <label
      className={`relative inline-flex h-11 items-center rounded-xl border text-sm font-medium transition ${
        inverse
          ? 'border-white/15 bg-white/[0.04] text-white hover:bg-white/[0.08]'
          : 'border-line bg-white text-muted hover:border-brand hover:text-ink'
      }`}
    >
      <Languages className="pointer-events-none absolute left-3" size={16} />
      <span className="sr-only">{t('language.label')}</span>
      <select
        aria-label={t('language.label')}
        className={`h-full cursor-pointer appearance-none bg-transparent pl-9 pr-8 outline-none ${compact ? 'w-[78px]' : 'w-[132px]'}`}
        onChange={(event) => void i18n.changeLanguage(event.target.value)}
        value={currentLanguage()}
      >
        {languages.map((language) => (
          <option key={language.code} value={language.code}>
            {compact ? language.shortLabel : language.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5" size={14} />
    </label>
  )
}
