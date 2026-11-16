import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import { useApplications } from '@/api/hooks'
import {
  INTERVIEW_OUTCOMES,
  INTERVIEW_TYPES,
  type Interview,
  type InterviewInput,
  type InterviewPatch,
} from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/Button'
import { Field, Input, Select, Textarea } from '@/components/ui/Field'
import { localDateTimeToIso, toDateInput, toTimeInput } from '@/lib/dates'

import { label } from './labels'

const schema = z.object({
  application_id: z.string().min(1, 'Choose the application'),
  date: z.string().min(1, 'Choose a date'),
  time: z.string().min(1, 'Choose a time'),
  duration_minutes: z
    .string()
    .regex(/^\d+$/, 'Use whole minutes')
    .refine((value) => Number(value) >= 1 && Number(value) <= 600, 'Use 1 to 600 minutes'),
  interview_type: z.enum(INTERVIEW_TYPES),
  outcome: z.enum(INTERVIEW_OUTCOMES),
  location: z.string().trim().max(500, 'Use at most 500 characters'),
  interviewer: z.string().trim().max(255, 'Use at most 255 characters'),
  notes: z.string().trim().max(5000, 'Use at most 5000 characters'),
})
type Values = z.infer<typeof schema>

interface InterviewFormProps {
  initial?: Interview
  defaultDate?: Date
  defaultApplicationId?: number
  submitLabel: string
  onCreate?: (input: InterviewInput) => Promise<unknown>
  onUpdate?: (input: InterviewPatch) => Promise<unknown>
  onCancel: () => void
}

export function InterviewForm({
  initial,
  defaultDate,
  defaultApplicationId,
  submitLabel,
  onCreate,
  onUpdate,
  onCancel,
}: InterviewFormProps) {
  const applications = useApplications({ sort: 'company', limit: 100 })
  const when = initial ? new Date(initial.scheduled_at) : defaultDate
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      application_id: String(initial?.application_id ?? defaultApplicationId ?? ''),
      date: when ? toDateInput(when) : '',
      time: initial ? toTimeInput(new Date(initial.scheduled_at)) : '10:00',
      duration_minutes: String(initial?.duration_minutes ?? 60),
      interview_type: initial?.interview_type ?? 'video',
      outcome: initial?.outcome ?? 'pending',
      location: initial?.location ?? '',
      interviewer: initial?.interviewer ?? '',
      notes: initial?.notes ?? '',
    },
  })
  const { errors, isSubmitting } = form.formState

  const submit = form.handleSubmit(async (values) => {
    const common = {
      scheduled_at: localDateTimeToIso(values.date, values.time),
      duration_minutes: Number(values.duration_minutes),
      interview_type: values.interview_type,
      outcome: values.outcome,
      location: values.location,
      interviewer: values.interviewer,
      notes: values.notes,
    }
    try {
      if (initial) await onUpdate?.(common)
      else await onCreate?.({ ...common, application_id: Number(values.application_id) })
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Saving failed'
      const field = error instanceof ApiError ? error.fieldErrors[0]?.field : undefined
      if (field === 'application_id') form.setError('application_id', { message })
      else form.setError('root', { message })
    }
  })

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      {errors.root?.message && <ErrorMessage error={new ApiError(400, errors.root.message)} />}
      <Field label="Application" error={errors.application_id?.message}>
        {(props) => (
          <Select {...props} {...form.register('application_id')} disabled={Boolean(initial) || applications.isPending}>
            <option value="">Choose an application…</option>
            {applications.data?.items.map((application) => (
              <option key={application.id} value={application.id}>
                {application.company} — {application.position}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Date" error={errors.date?.message}>
          {(props) => <Input type="date" {...props} {...form.register('date')} />}
        </Field>
        <Field label="Time" error={errors.time?.message}>
          {(props) => <Input type="time" {...props} {...form.register('time')} />}
        </Field>
        <Field label="Duration (minutes)" error={errors.duration_minutes?.message}>
          {(props) => (
            <Input
              type="number"
              inputMode="numeric"
              min={1}
              max={600}
              {...props}
              {...form.register('duration_minutes')}
            />
          )}
        </Field>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Type" error={errors.interview_type?.message}>
          {(props) => (
            <Select {...props} {...form.register('interview_type')}>
              {INTERVIEW_TYPES.map((type) => (
                <option key={type} value={type}>
                  {label(type)}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Outcome" error={errors.outcome?.message}>
          {(props) => (
            <Select {...props} {...form.register('outcome')}>
              {INTERVIEW_OUTCOMES.map((outcome) => (
                <option key={outcome} value={outcome}>
                  {label(outcome)}
                </option>
              ))}
            </Select>
          )}
        </Field>
      </div>
      <Field label="Location or meeting link" error={errors.location?.message}>
        {(props) => <Input {...props} {...form.register('location')} />}
      </Field>
      <Field label="Interviewer" error={errors.interviewer?.message}>
        {(props) => <Input {...props} {...form.register('interviewer')} />}
      </Field>
      <Field label="Notes" error={errors.notes?.message}>
        {(props) => <Textarea {...props} {...form.register('notes')} />}
      </Field>
      <p className="text-xs text-slate-500">
        Times are in your time zone ({Intl.DateTimeFormat().resolvedOptions().timeZone}).
      </p>
      <div className="flex justify-end gap-3">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
