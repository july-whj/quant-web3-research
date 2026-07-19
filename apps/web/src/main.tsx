import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-sans/700.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './i18n'
import { AppProviders } from './app/providers'
import { AppRouter } from './app/router'
import './styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProviders>
      <AppRouter />
    </AppProviders>
  </StrictMode>,
)
