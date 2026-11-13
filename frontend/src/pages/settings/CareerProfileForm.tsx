import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import { useCareerProfile, useSaveCareerProfile } from '@/api/hooks'
import type { CareerProfile } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/Button'
import { Field, Input, Textarea } from '@/components/ui/Field'
import { Spinner } from '@/components/ui/Spinner'

function splitSkills(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((skill) => skill.trim())
    .filter(Boolean)
}

const schema = z.object({
  headline: z.string().trim().max(255, 'Use at most 255 characters'),
  target_role: z.string().trim().max(255, 'Use at most 255 characters'),
  years_experience: z
    .string()
    .trim()
    .refine((v) => v === '' || (/^\d+$/.test(v) && Number(v) <= 60), 'Use a whole number from 0 to 60'),
  skills: z
    .string()
    .refine((v) => splitSkills(v).length <= 100, 'Use at most 100 skills')
    .refine((v) => splitSkills(v).every((s) => s.length <= 60), 'Each skill can have at most 60 characters'),
  cv_text: z.string().trim().max(30000, 'Use at most 30,000 characters'),
})
type Values = z.infer<typeof schema>
const FIELDS = ['headline', 'target_role', 'years_experience', 'skills', 'cv_text'] as const

function toValues(profile?: CareerProfile): Values {
  return {
    headline: profile?.headline ?? '',
    target_role: profile?.target_role ?? '',
    years_experience: profile?.years_experience == null ? '' : String(profile.years_experience),
    skills: profile?.skills.join(', ') ?? '',
    cv_text: profile?.cv_text ?? '',
  }
}

export function CareerProfileForm() {
  const profile = useCareerProfile()
  const save = useSaveCareerProfile()
  const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: toValues() })
  const { errors, isSubmitting, isDirty } = form.formState
  const cvText = useWatch({ control: form.control, name: 'cv_text' })

  useEffect(() => {
    if (profile.data) form.reset(toValues(profile.data))
  }, [profile.data, form])

  const submit = form.handleSubmit(async (values) => {
    try {
      const saved = await save.mutateAsync({
        headline: values.headline,
        target_role: values.target_role,
        years_experience: values.years_experience === '' ? null : Number(values.years_experience),
        skills: splitSkills(values.skills),
        cv_text: values.cv_text,
      })
      form.reset(toValues(saved))
      toast.success('Career profile saved')
    } catch (error) {
      const fieldErrors = error instanceof ApiError ? error.fieldErrors : []
      const known = fieldErrors.filter((e) => (FIELDS as readonly string[]).includes(e.field))
      if (known.length) {
        for (const { field, message } of known) form.setError(field as (typeof FIELDS)[number], { message })
      } else {
        form.setError('root', { message: error instanceof ApiError ? error.message : 'Saving failed' })
      }
    }
  })

  if (profile.error) return <ErrorMessage error={profile.error} onRetry={() => profile.refetch()} />
  if (profile.isPending) return <Spinner label="Loading career profile" />

  const cvWords = cvText.trim().split(/\s+/).filter(Boolean).length
  const unrecognized = profile.data.unrecognized_skills

  return (
    <form onSubmit={submit} className="space-y-4" noValidate aria-label="Career profile">
      {errors.root?.message && <ErrorMessage error={new ApiError(400, errors.root.message)} />}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Headline" error={errors.headline?.message} className="sm:col-span-2">
          {(props) => (
            <Input placeholder="Backend developer focused on Python APIs" {...props} {...form.register('headline')} />
          )}
        </Field>
        <Field label="Target role" error={errors.target_role?.message}>
          {(props) => <Input placeholder="Backend Engineer" {...props} {...form.register('target_role')} />}
        </Field>
        <Field label="Years of experience" error={errors.years_experience?.message}>
          {(props) => <Input inputMode="numeric" {...props} {...form.register('years_experience')} />}
        </Field>
        <Field
          label="Skills"
          error={errors.skills?.message}
          hint="Separate with commas, e.g. Python, FastAPI, PostgreSQL, Docker"
          className="sm:col-span-2"
        >
          {(props) => <Textarea rows={2} {...props} {...form.register('skills')} />}
        </Field>
      </div>
      {profile.data.recognized_skills.length > 0 && (
        <div className="text-sm">
          <p className="font-medium text-slate-700">Recognised by the assistant (from skills and CV)</p>
          <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Recognised skills">
            {profile.data.recognized_skills.map((skill) => (
              <li key={skill} className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">
                {skill}
              </li>
            ))}
          </ul>
          {unrecognized.length > 0 && (
            <p className="mt-2 text-xs text-slate-500">
              Not in the skill list yet (kept, but not scored): {unrecognized.join(', ')}
            </p>
          )}
        </div>
      )}
      <Field
        label="CV (plain text)"
        error={errors.cv_text?.message}
        hint={`${cvWords} words. Paste your CV text; it stays private and is only analysed on this server.`}
      >
        {(props) => <Textarea rows={10} {...props} {...form.register('cv_text')} />}
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={isSubmitting} disabled={!isDirty}>
          Save career profile
        </Button>
      </div>
    </form>
  )
}
