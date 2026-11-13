import { zodResolver } from '@hookform/resolvers/zod'
import type { ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/context'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Logo } from '@/components/Logo'
import { Button } from '@/components/ui/Button'
import { Field, Input } from '@/components/ui/Field'

function AuthShell({ title, subtitle, children }: { title: string; subtitle: ReactNode; children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12">
      <Logo />
      <div className="mt-8 w-full max-w-sm rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </div>
    </div>
  )
}

// ------------------------------------------------------------------- login

const loginSchema = z.object({
  email: z.string().trim().min(1, 'Enter your email').email('Enter a valid email address'),
  password: z.string().min(1, 'Enter your password'),
})
type LoginValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'
  const form = useForm<LoginValues>({ resolver: zodResolver(loginSchema), defaultValues: { email: '', password: '' } })
  const { errors, isSubmitting } = form.formState

  const onSubmit = form.handleSubmit(async ({ email, password }) => {
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (error) {
      form.setError('root', { message: error instanceof ApiError ? error.message : 'Sign-in failed' })
    }
  })

  return (
    <AuthShell
      title="Sign in"
      subtitle={
        <>
          New to CareerOps?{' '}
          <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {errors.root?.message && <ErrorMessage error={new ApiError(400, errors.root.message)} />}
        <Field label="Email" error={errors.email?.message}>
          {(props) => <Input type="email" autoComplete="email" {...props} {...form.register('email')} />}
        </Field>
        <Field label="Password" error={errors.password?.message}>
          {(props) => (
            <Input type="password" autoComplete="current-password" {...props} {...form.register('password')} />
          )}
        </Field>
        <Button type="submit" className="w-full" loading={isSubmitting}>
          Sign in
        </Button>
      </form>
    </AuthShell>
  )
}

// ---------------------------------------------------------------- register

const registerSchema = z.object({
  full_name: z.string().trim().max(255, 'Use at most 255 characters'),
  email: z.string().trim().min(1, 'Enter your email').email('Enter a valid email address'),
  password: z
    .string()
    .min(8, 'Use at least 8 characters')
    .max(128, 'Use at most 128 characters')
    .refine((value) => !/^\d+$/.test(value) && !/^\p{L}+$/u.test(value), {
      message: 'Mix letters with numbers or symbols',
    }),
})
type RegisterValues = z.infer<typeof registerSchema>

export function RegisterPage() {
  const { register: createAccount } = useAuth()
  const navigate = useNavigate()
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: '', email: '', password: '' },
  })
  const { errors, isSubmitting } = form.formState

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      await createAccount(values)
      toast.success('Welcome to CareerOps!')
      navigate('/dashboard', { replace: true })
    } catch (error) {
      if (error instanceof ApiError && error.fieldErrors.length) {
        for (const { field, message } of error.fieldErrors) {
          if (field === 'email' || field === 'password' || field === 'full_name') form.setError(field, { message })
        }
      } else {
        form.setError('root', { message: error instanceof ApiError ? error.message : 'Registration failed' })
      }
    }
  })

  return (
    <AuthShell
      title="Create your account"
      subtitle={
        <>
          Already have one?{' '}
          <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {errors.root?.message && <ErrorMessage error={new ApiError(400, errors.root.message)} />}
        <Field label="Full name (optional)" error={errors.full_name?.message}>
          {(props) => <Input autoComplete="name" {...props} {...form.register('full_name')} />}
        </Field>
        <Field label="Email" error={errors.email?.message}>
          {(props) => <Input type="email" autoComplete="email" {...props} {...form.register('email')} />}
        </Field>
        <Field
          label="Password"
          error={errors.password?.message}
          hint="At least 8 characters, mixing letters with numbers or symbols."
        >
          {(props) => <Input type="password" autoComplete="new-password" {...props} {...form.register('password')} />}
        </Field>
        <Button type="submit" className="w-full" loading={isSubmitting}>
          Create account
        </Button>
      </form>
    </AuthShell>
  )
}
