import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { AuthLayout } from './AuthLayout'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'

const schema = z.object({
  email: z.email('Please enter a valid work email address'),
})

export function ForgotPasswordPage() {
  const [done, setDone] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: '' },
  })

  async function onSubmit(values) {
    try {
      await api.post('/auth/password-reset/', values)
    } catch {
      /* still show generic success */
    }
    setDone(true)
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="We’ll send a reset link if that email belongs to an account."
      footer={
        <Link to="/login" className="font-semibold text-brand hover:underline">
          Back to sign in
        </Link>
      }
    >
      {done ? (
        <p className="rounded-lg border border-border bg-mint/50 px-3 py-3 text-sm text-ink">
          If an account exists, a reset link has been dispatched.
        </p>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-ink">
              Work email
            </span>
            <input
              type="email"
              autoComplete="email"
              className={`w-full rounded-lg border bg-paper px-3 py-2.5 text-sm text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
                errors.email ? 'border-red-400' : 'border-border'
              }`}
              {...register('email')}
            />
            {errors.email?.message ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.email.message}
              </span>
            ) : null}
          </label>
          <Button type="submit" className="w-full py-3" disabled={isSubmitting}>
            {isSubmitting ? 'Sending…' : 'Send reset link'}
          </Button>
        </form>
      )}
    </AuthLayout>
  )
}
