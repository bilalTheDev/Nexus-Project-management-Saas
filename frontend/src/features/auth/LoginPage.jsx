import { useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'
import { AuthLayout } from './AuthLayout'
import { loginSchema } from './schemas'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'

const DEMO_USERS = [
  {
    label: 'Maya Lin (Lead Owner)',
    email: 'maya@northstar.studio',
    password: 'DemoPass1',
  },
  {
    label: 'Daniel Vance (Developer)',
    email: 'daniel@northstar.studio',
    password: 'DemoPass1',
  },
]

export function LoginPage() {
  const { login, isAuthenticated, bootstrapping } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const inviteToken = params.get('invite') || ''
  const [showPassword, setShowPassword] = useState(false)
  const [formError, setFormError] = useState('')
  const [demoLoading, setDemoLoading] = useState('')

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: params.get('email') || '',
      password: '',
      rememberMe: false,
    },
  })

  if (!bootstrapping && isAuthenticated) {
    if (inviteToken) {
      return <Navigate to={`/invite/${inviteToken}`} replace />
    }
    return <Navigate to="/app" replace />
  }

  async function completeLogin(email, password) {
    const session = await login({ email, password })
    if (inviteToken) {
      navigate(`/invite/${inviteToken}`, { replace: true })
      return
    }
    const dest = session.default_workspace
      ? `/app/${session.default_workspace}/dashboard`
      : '/app/workspaces/new'
    navigate(dest, { replace: true })
  }

  async function onSubmit(values) {
    setFormError('')
    try {
      await completeLogin(values.email, values.password)
    } catch (err) {
      setFormError(
        authErrorMessage(err, 'Invalid email or password. Please try again.'),
      )
    }
  }

  function authErrorMessage(err, fallback) {
    const data = err.response?.data
    const detail = data?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
    if (err.response?.status === 429) {
      return 'Too many sign-in attempts. Wait a minute and try again.'
    }
    if (!err.response) {
      return 'Cannot reach the API. Start the backend (port 8000) and use the same host as Vite (localhost vs 127.0.0.1).'
    }
    if (err.response.status === 401) {
      return `${fallback} If this persists, run: python manage.py seed_demo_users`
    }
    return fallback
  }

  async function signInAsDemo(user) {
    setFormError('')
    setDemoLoading(user.email)
    setValue('email', user.email, { shouldValidate: true, shouldDirty: true })
    setValue('password', user.password, {
      shouldValidate: true,
      shouldDirty: true,
    })
    try {
      await completeLogin(user.email, user.password)
    } catch (err) {
      setFormError(
        authErrorMessage(
          err,
          'Demo sign-in failed. Seed demo users with: python manage.py seed_demo_users',
        ),
      )
    } finally {
      setDemoLoading('')
    }
  }

  const isDemo = params.get('demo') === 'true'
  const busy = isSubmitting || Boolean(demoLoading)

  return (
    <AuthLayout
      title="Welcome back to Nexus"
      subtitle="Sign in to continue planning with your workspace."
      footer={
        <>
          New here?{' '}
          <Link
            to="/signup"
            className="font-semibold text-brand underline-offset-2 hover:underline"
          >
            Create an account
          </Link>
        </>
      }
    >
      <div
        className={`mb-6 rounded-xl border border-brand/25 bg-mint/60 p-3 ${
          isDemo ? 'ring-1 ring-brand/30' : ''
        }`}
      >
        <p className="text-xs font-semibold text-ink">Demo Evaluator</p>
        <p className="mt-1 text-xs text-ink-secondary">
          One-click sign-in with a seeded portfolio account. Password for both:{' '}
          <span className="font-mono text-ink">DemoPass1</span>
        </p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          {DEMO_USERS.map((user) => (
            <button
              key={user.email}
              type="button"
              disabled={busy}
              onClick={() => signInAsDemo(user)}
              className="btn-lift rounded-lg border border-border bg-surface-raised px-3 py-2 text-left text-xs font-medium text-ink shadow-hairline hover:bg-surface-low focus-ring disabled:opacity-60"
            >
              {demoLoading === user.email
                ? `Signing in as ${user.label.split(' (')[0]}…`
                : user.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {formError ? (
          <div
            role="alert"
            className="rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger"
          >
            {formError}
          </div>
        ) : null}

        <Field label="Work email" error={errors.email?.message}>
          <input
            type="email"
            autoComplete="email"
            className={inputClass(errors.email)}
            {...register('email')}
          />
        </Field>

        <Field label="Password" error={errors.password?.message}>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              className={`${inputClass(errors.password)} pr-11`}
              {...register('password')}
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-ink-muted hover:text-ink focus-ring"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </Field>

        <div className="flex items-center justify-between gap-3">
          <label className="inline-flex items-center gap-2 text-sm text-ink-secondary">
            <input
              type="checkbox"
              className="size-4 rounded border-border text-brand focus:ring-brand"
              {...register('rememberMe')}
            />
            Remember this device
          </label>
          <Link
            to="/forgot-password"
            className="text-sm font-medium text-brand hover:underline"
          >
            Forgot password?
          </Link>
        </div>

        <Button type="submit" className="w-full py-3" disabled={busy}>
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
    </AuthLayout>
  )
}

function Field({ label, error, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-ink">{label}</span>
      {children}
      {error ? (
        <span className="mt-1 block text-xs text-danger">{error}</span>
      ) : null}
    </label>
  )
}

function inputClass(error) {
  return `w-full rounded-lg border bg-surface-low px-3 py-2.5 text-sm text-ink placeholder:text-ink-muted shadow-hairline focus:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
    error ? 'border-danger' : 'border-border'
  }`
}
