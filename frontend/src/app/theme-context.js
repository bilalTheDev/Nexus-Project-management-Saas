import { createContext } from 'react'

export const ThemeContext = createContext(null)

export const STORAGE_KEY = 'nexus-theme'

export function getPreferredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    /* ignore */
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'
  }
  return 'light'
}

export function applyTheme(theme) {
  const root = document.documentElement
  root.setAttribute('data-theme', theme)
  root.style.colorScheme = theme === 'dark' ? 'dark' : 'light'
}

/** Toggle theme with optional circular view-transition from a click point. */
export function toggleThemeWithTransition(nextTheme, originEvent) {
  const reduceMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const apply = () => {
    applyTheme(nextTheme)
    try {
      localStorage.setItem(STORAGE_KEY, nextTheme)
    } catch {
      /* ignore */
    }
  }

  if (
    reduceMotion ||
    typeof document.startViewTransition !== 'function' ||
    !originEvent
  ) {
    apply()
    return
  }

  const x = originEvent.clientX
  const y = originEvent.clientY
  const root = document.documentElement
  root.style.setProperty('--theme-x', `${x}px`)
  root.style.setProperty('--theme-y', `${y}px`)
  root.classList.add('theme-vt-active')

  const transition = document.startViewTransition(() => {
    apply()
  })

  transition.finished.finally(() => {
    root.classList.remove('theme-vt-active')
  })
}
