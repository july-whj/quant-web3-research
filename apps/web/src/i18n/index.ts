import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import { en } from './locales/en'
import { ja } from './locales/ja'
import { zhCN } from './locales/zh-CN'
import { zhTW } from './locales/zh-TW'

export const supportedLanguages = ['zh-CN', 'zh-TW', 'ja', 'en'] as const
export type AppLanguage = (typeof supportedLanguages)[number]

const storageKey = 'qwr_language'

function resolveLanguage(value: string | null | undefined): AppLanguage | null {
  if (!value) return null
  const language = value.toLowerCase()
  if (language === 'zh-tw' || language.startsWith('zh-hk') || language.startsWith('zh-mo') || language.includes('hant')) return 'zh-TW'
  if (language.startsWith('zh')) return 'zh-CN'
  if (language.startsWith('ja')) return 'ja'
  if (language.startsWith('en')) return 'en'
  return null
}

function detectInitialLanguage(): AppLanguage {
  const stored = resolveLanguage(window.localStorage.getItem(storageKey))
  if (stored) return stored
  for (const language of navigator.languages ?? [navigator.language]) {
    const resolved = resolveLanguage(language)
    if (resolved) return resolved
  }
  return 'zh-CN'
}

void i18n.use(initReactI18next).init({
  resources: {
    'zh-CN': { translation: zhCN },
    'zh-TW': { translation: zhTW },
    ja: { translation: ja },
    en: { translation: en },
  },
  lng: detectInitialLanguage(),
  fallbackLng: 'zh-CN',
  supportedLngs: supportedLanguages,
  load: 'currentOnly',
  interpolation: { escapeValue: false },
  react: { useSuspense: false },
})

function applyDocumentLanguage(language: string) {
  const resolved = resolveLanguage(language) ?? 'zh-CN'
  window.localStorage.setItem(storageKey, resolved)
  document.documentElement.lang = resolved
  document.title = i18n.t('meta.title')
}

applyDocumentLanguage(i18n.resolvedLanguage ?? i18n.language)
i18n.on('languageChanged', applyDocumentLanguage)

export function currentLanguage(): AppLanguage {
  return resolveLanguage(i18n.resolvedLanguage ?? i18n.language) ?? 'zh-CN'
}

export default i18n
