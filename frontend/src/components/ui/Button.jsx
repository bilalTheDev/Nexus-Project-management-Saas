import { Link } from 'react-router-dom'

const variants = {
  primary:
    'bg-ink text-paper hover:bg-[#263B4A] border border-transparent shadow-sm',
  secondary:
    'bg-surface text-ink border border-border hover:border-border-strong hover:bg-surface-low',
  ghost:
    'bg-transparent text-ink-secondary hover:text-ink border border-transparent',
}

const base =
  'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors focus-ring disabled:opacity-50'

export function Button({
  variant = 'primary',
  className = '',
  children,
  to,
  type = 'button',
  ...rest
}) {
  const classes = `${base} ${variants[variant]} ${className}`

  if (to) {
    return (
      <Link to={to} className={classes} {...rest}>
        {children}
      </Link>
    )
  }

  return (
    <button type={type} className={classes} {...rest}>
      {children}
    </button>
  )
}
