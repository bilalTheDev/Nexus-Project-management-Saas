import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { toggleThemeWithTransition } from '@/app/theme-context'

export function ThemeToggleButton({ className = '' }) {
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
      className={`inline-flex size-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-muted)] focus-ring hover:text-[var(--text)] ${className}`}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={isDark ? 'Light theme' : 'Dark theme'}
    >
      {isDark ? <Sun size={16} aria-hidden /> : <Moon size={16} aria-hidden />}
    </button>
  )
}
