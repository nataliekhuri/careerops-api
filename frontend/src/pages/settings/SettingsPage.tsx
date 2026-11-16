import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import { useChangePassword, useDeleteAccount, useUpdateProfile } from '@/api/hooks'
import { useAuth } from '@/auth/context'
import { Button } from '@/components/ui/Button'
import { Card, PageHeader } from '@/components/ui/Card'
import { Field, Input } from '@/components/ui/Field'
import { formatDate } from '@/lib/format'

import { CareerProfileForm } from './CareerProfileForm'

const newPassword = z
  .string()
  .min(8, 'Use at least 8 characters')
  .max(128, 'Use at most 128 characters')
  .refine((value) => !/^\d+$/.test(value) && !/^\p{L}+$/u.test(value), {
    message: 'Mix letters with numbers or symbols',
  })

function Section({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <Card className="grid gap-6 p-6 md:grid-cols-3">
      <div>
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      </div>
      <div className="md:col-span-2">{children}</div>
    </Card>
  )
}

function ProfileForm() {
  const { user } = useAuth()
  const update = useUpdateProfile()
  const form = useForm<{ full_name: string }>({
    resolver: zodResolver(z.object({ full_name: z.string().trim().max(255, 'Use at most 255 characters') })),
    defaultValues: { full_name: user?.full_name ?? '' },
  })
  const { errors, isSubmitting, isDirty } = form.formState

  const submit = form.handleSubmit(async ({ full_name }) => {
    try {
      const saved = await update.mutateAsync(full_name)
      form.reset({ full_name: saved.full_name })
      toast.success('Profile saved')
    } catch (error) {
      form.setError('full_name', { message: error instanceof ApiError ? error.message : 'Saving failed' })
    }
  })

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <Field label="Full name" error={errors.full_name?.message}>
        {(props) => <Input autoComplete="name" {...props} {...form.register('full_name')} />}
      </Field>
      <Field label="Email" hint="Your email is your sign-in name and can't be changed.">
        {(props) => <Input type="email" value={user?.email ?? ''} readOnly disabled {...props} />}
      </Field>
      {user && <p className="text-xs text-slate-500">Member since {formatDate(user.created_at)}</p>}
      <div className="flex justify-end">
        <Button type="submit" loading={isSubmitting} disabled={!isDirty}>
          Save profile
        </Button>
      </div>
    </form>
  )
}

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Enter your current password'),
    new_password: newPassword,
    confirm: z.string(),
  })
  .refine((v) => v.new_password === v.confirm, { path: ['confirm'], message: 'Passwords do not match' })
type PasswordValues = z.infer<typeof passwordSchema>

function PasswordForm() {
  const change = useChangePassword()
  const form = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: '', new_password: '', confirm: '' },
  })
  const { errors, isSubmitting } = form.formState

  const submit = form.handleSubmit(async ({ current_password, new_password }) => {
    try {
      await change.mutateAsync({ current_password, new_password })
      form.reset()
      toast.success('Password changed')
    } catch (error) {
      if (error instanceof ApiError && error.status === 400) {
        form.setError('current_password', { message: error.message })
      } else if (error instanceof ApiError && error.fieldErrors.some((e) => e.field === 'new_password')) {
        form.setError('new_password', { message: error.fieldErrors.find((e) => e.field === 'new_password')!.message })
      } else {
        form.setError('current_password', { message: error instanceof ApiError ? error.message : 'Change failed' })
      }
    }
  })

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <Field label="Current password" error={errors.current_password?.message}>
        {(props) => (
          <Input type="password" autoComplete="current-password" {...props} {...form.register('current_password')} />
        )}
      </Field>
      <Field
        label="New password"
        error={errors.new_password?.message}
        hint="At least 8 characters, mixing letters with numbers or symbols."
      >
        {(props) => <Input type="password" autoComplete="new-password" {...props} {...form.register('new_password')} />}
      </Field>
      <Field label="Confirm new password" error={errors.confirm?.message}>
        {(props) => <Input type="password" autoComplete="new-password" {...props} {...form.register('confirm')} />}
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={isSubmitting}>
          Change password
        </Button>
      </div>
    </form>
  )
}

function DeleteAccount() {
  const { logout } = useAuth()
  const remove = useDeleteAccount()
  const [password, setPassword] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onDelete(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await remove.mutateAsync(password)
      logout('/') // the route guard then sends the user to the landing page
      toast.success('Your account and all its data have been deleted')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Deletion failed')
    }
  }

  return (
    <form onSubmit={onDelete} className="space-y-4" noValidate>
      <p className="text-sm text-slate-600">
        This permanently deletes your account, applications, companies and interviews. It cannot be undone.
      </p>
      <Field label="Password" error={error ?? undefined}>
        {(props) => (
          <Input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            {...props}
          />
        )}
      </Field>
      <label className="flex items-start gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
          className="mt-0.5 size-4 rounded border-slate-300 text-red-600 focus:ring-red-500"
        />
        I understand that all my data will be permanently deleted.
      </label>
      <div className="flex justify-end">
        <Button type="submit" variant="danger" disabled={!confirmed || !password} loading={remove.isPending}>
          Delete my account
        </Button>
      </div>
    </form>
  )
}

export function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" description="Manage your profile, career profile, password and account." />
      <div className="space-y-6">
        <Section title="Profile" description="How your name appears in CareerOps.">
          <ProfileForm />
        </Section>
        <div id="career-profile" className="scroll-mt-6">
          <Section
            title="Career profile"
            description="Your skills, experience and CV. The AI assistant uses them to score job matches and review your CV."
          >
            <CareerProfileForm />
          </Section>
        </div>
        <Section title="Password" description="Use a long password you don't use anywhere else.">
          <PasswordForm />
        </Section>
        <Section title="Delete account" description="Remove your account and everything in it.">
          <DeleteAccount />
        </Section>
      </div>
    </>
  )
}
