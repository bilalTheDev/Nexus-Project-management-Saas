import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ThemeContext,
  STORAGE_KEY,
  applyTheme,
  getPreferredTheme,
} from './theme-context'
// applyTheme keeps <html data-theme> + color-scheme in sync with React state

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    if (typeof document !== 'undefined') {
      const current = document.documentElement.getAttribute('data-theme')
      if (current === 'light' || current === 'dark') return current
    }
    return getPreferredTheme()
  })

  useEffect(() => {
    applyTheme(theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      /* ignore */
    }
  }, [theme])

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = (event) => {
      try {
        if (localStorage.getItem(STORAGE_KEY)) return
      } catch {
        /* ignore */
      }
      setThemeState(event.matches ? 'dark' : 'light')
    }
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  const setTheme = useCallback((next) => {
    const resolved = next === 'dark' ? 'dark' : 'light'
    applyTheme(resolved)
    setThemeState(resolved)
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }, [setTheme, theme])

  const value = useMemo(
    () => ({ theme, setTheme, toggleTheme, isDark: theme === 'dark' }),
    [theme, setTheme, toggleTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
