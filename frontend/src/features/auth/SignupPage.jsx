import { useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'
import { AuthLayout } from './AuthLayout'
import { passwordStrength, signupSchema } from './schemas'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'

export function SignupPage() {
  const { register: registerUser, isAuthenticated, bootstrapping } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [showPassword, setShowPassword] = useState(false)
  const [formError, setFormError] = useState('')

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      full_name: '',
      email: params.get('email') || '',
      password: '',
      confirm_password: '',
      accept_terms: false,
    },
  })

  const passwordValue = watch('password') || ''
  const strength = useMemo(() => passwordStrength(passwordValue), [passwordValue])

  if (!bootstrapping && isAuthenticated) {
    return <Navigate to="/app/workspaces/new" replace />
  }

  async function onSubmit(values) {
    setFormError('')
    try {
      await registerUser({
        email: values.email,
        password: values.password,
        full_name: values.full_name,
      })
      navigate('/app/workspaces/new', { replace: true })
    } catch (err) {
      const data = err.response?.data
      const detail =
        data?.email?.[0] ||
        data?.password?.[0] ||
        data?.detail ||
        'Could not create your account. Please try again.'
      setFormError(typeof detail === 'string' ? detail : 'Sign up failed.')
    }
  }

  return (
    <AuthLayout
      title="Create your Nexus account"
      subtitle="Start a workspace for your team in a few minutes."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-brand underline-offset-2 hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {formError ? (
          <div
            role="alert"
            className="rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger"
          >
            {formError}
          </div>
        ) : null}

        <Field label="Full name" error={errors.full_name?.message}>
          <input
            type="text"
            autoComplete="name"
            className={inputClass(errors.full_name)}
            {...register('full_name')}
          />
        </Field>

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
              autoComplete="new-password"
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
          <StrengthMeter score={strength} />
        </Field>

        <Field label="Confirm password" error={errors.confirm_password?.message}>
          <input
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className={inputClass(errors.confirm_password)}
            {...register('confirm_password')}
          />
        </Field>

        <label className="flex items-start gap-2 text-sm text-ink-secondary">
          <input
            type="checkbox"
            className="mt-0.5 size-4 rounded border-border text-brand focus:ring-brand"
            {...register('accept_terms')}
          />
          <span>
            I agree to the terms of use and acknowledge this is a portfolio demo
            environment.
          </span>
        </label>
        {errors.accept_terms?.message ? (
          <p className="-mt-2 text-xs text-danger">{errors.accept_terms.message}</p>
        ) : null}

        <Button type="submit" className="w-full py-3" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
    </AuthLayout>
  )
}

function StrengthMeter({ score }) {
  const labels = ['Too weak', 'Weak', 'Okay', 'Strong', 'Excellent']
  return (
    <div className="mt-2">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <span
            key={i}
            className={`h-1.5 flex-1 rounded-full ${
              i < score ? 'bg-brand' : 'bg-border'
            }`}
          />
        ))}
      </div>
      <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-ink-muted">
        {labels[score] || labels[0]}
      </p>
    </div>
  )
}

function Field({ label, error, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-ink">{label}</span>
      {children}
      {error ? <span className="mt-1 block text-xs text-danger">{error}</span> : null}
    </label>
  )
}

function inputClass(error) {
  return `w-full rounded-lg border bg-surface-low px-3 py-2.5 text-sm text-ink placeholder:text-ink-muted shadow-hairline focus:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
    error ? 'border-danger' : 'border-border'
  }`
}
