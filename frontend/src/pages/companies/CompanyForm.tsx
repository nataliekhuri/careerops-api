import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import type { Company, CompanyInput } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/Button'
import { Field, Input, Textarea } from '@/components/ui/Field'

const schema = z.object({
  name: z.string().trim().min(1, 'Enter the company name').max(255, 'Use at most 255 characters'),
  website: z
    .string()
    .trim()
    .max(500, 'Use at most 500 characters')
    .refine((v) => v === '' || /^https?:\/\//i.test(v), 'Start with http:// or https://'),
  industry: z.string().trim().max(100, 'Use at most 100 characters'),
  location: z.string().trim().max(255, 'Use at most 255 characters'),
  notes: z.string().trim().max(5000, 'Use at most 5000 characters'),
})
type Values = z.infer<typeof schema>
const FIELDS = ['name', 'website', 'industry', 'location', 'notes'] as const

interface CompanyFormProps {
  initial?: Company
  submitLabel: string
  onSubmit: (input: CompanyInput) => Promise<unknown>
  onCancel: () => void
}

export function CompanyForm({ initial, submitLabel, onSubmit, onCancel }: CompanyFormProps) {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name ?? '',
      website: initial?.website ?? '',
      industry: initial?.industry ?? '',
      location: initial?.location ?? '',
      notes: initial?.notes ?? '',
    },
  })
  const { errors, isSubmitting } = form.formState

  const submit = form.handleSubmit(async (values) => {
    try {
      await onSubmit(values)
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        form.setError('name', { message: error.message })
      } else if (error instanceof ApiError && error.fieldErrors.length) {
        for (const { field, message } of error.fieldErrors) {
          if ((FIELDS as readonly string[]).includes(field))
            form.setError(field as (typeof FIELDS)[number], { message })
        }
      } else {
        form.setError('root', { message: error instanceof ApiError ? error.message : 'Saving failed' })
      }
    }
  })

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      {errors.root?.message && <ErrorMessage error={new ApiError(400, errors.root.message)} />}
      <Field label="Name" error={errors.name?.message}>
        {(props) => <Input autoComplete="organization" {...props} {...form.register('name')} />}
      </Field>
      <Field label="Website" error={errors.website?.message}>
        {(props) => <Input type="url" placeholder="https://" {...props} {...form.register('website')} />}
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Industry" error={errors.industry?.message}>
          {(props) => <Input {...props} {...form.register('industry')} />}
        </Field>
        <Field label="Location" error={errors.location?.message}>
          {(props) => <Input {...props} {...form.register('location')} />}
        </Field>
      </div>
      <Field label="Notes" error={errors.notes?.message}>
        {(props) => <Textarea {...props} {...form.register('notes')} />}
      </Field>
      <div className="flex justify-end gap-3 pt-2">
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
