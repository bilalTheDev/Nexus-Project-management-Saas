import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { toggleThemeWithTransition } from '@/app/theme-context'

export function ThemeToggle({ className = '' }) {
  const { theme, setTheme, isDark } = useTheme()

  function onToggle(event) {
    const next = theme === 'dark' ? 'light' : 'dark'
    toggleThemeWithTransition(next, event)
    setTheme(next)
  }

  return (
    <button
      type="button"
      onClick={onToggle}
      className={`btn-lift inline-flex size-9 items-center justify-center rounded-lg border border-border bg-surface-raised text-ink shadow-hairline hover:bg-surface-low focus-ring ${className}`}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Light mode' : 'Dark mode'}
    >
      {isDark ? <Sun size={16} strokeWidth={1.75} /> : <Moon size={16} strokeWidth={1.75} />}
    </button>
  )
}
