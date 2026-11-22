import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import { I18nProvider } from './contexts/I18nContext.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'

async function initApp() {
  const isDemoMode =
    typeof window !== 'undefined' &&
    (window.location.hostname.endsWith(".github.io") ||
      window.location.search.includes("demo=true") ||
      import.meta.env.VITE_DEMO === "true" ||
      import.meta.env.VITE_DEMO_MODE === "true");

  if (isDemoMode) {
    await import('./mockApi.js');
  }

  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <ErrorBoundary>
        <I18nProvider>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </I18nProvider>
      </ErrorBoundary>
    </StrictMode>,
  );
}

initApp();
