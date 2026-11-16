import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import { useCompanies } from '@/api/hooks'
import { APPLICATION_STATUSES, type Application, type ApplicationInput } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/Button'
import { Field, Input, Select, Textarea } from '@/components/ui/Field'

// Mirrors the API's validation so most mistakes are caught before sending.
const schema = z.object({
  company: z.string().trim().min(1, 'Enter the company name').max(255, 'Use at most 255 characters'),
  position: z.string().trim().min(1, 'Enter the job title').max(255, 'Use at most 255 characters'),
  location: z.string().trim().min(1, 'Enter a location or "Remote"').max(255, 'Use at most 255 characters'),
  status: z.enum(APPLICATION_STATUSES),
  company_id: z.string(),
  notes: z.string().trim().max(5000, 'Use at most 5000 characters'),
})
type Values = z.infer<typeof schema>

const FIELDS = ['company', 'position', 'location', 'status', 'company_id', 'notes'] as const

interface ApplicationFormProps {
  initial?: Application
  submitLabel: string
  onSubmit: (input: ApplicationInput) => Promise<unknown>
  onCancel?: () => void
}

export function ApplicationForm({ initial, submitLabel, onSubmit, onCancel }: ApplicationFormProps) {
  const companies = useCompanies({ limit: 100, sort: 'name' })
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      company: initial?.company ?? '',
      position: initial?.position ?? '',
      location: initial?.location ?? '',
      status: initial?.status ?? 'Applied',
      company_id: initial?.company_id ? String(initial.company_id) : '',
      notes: initial?.notes ?? '',
    },
  })
  const { errors, isSubmitting } = form.formState

  const submit = form.handleSubmit(async (values) => {
    try {
      await onSubmit({ ...values, company_id: values.company_id ? Number(values.company_id) : null })
    } catch (error) {
      if (error instanceof ApiError && error.fieldErrors.some((e) => (FIELDS as readonly string[]).includes(e.field))) {
        for (const { field, message } of error.fieldErrors) {
          if ((FIELDS as readonly string[]).includes(field))
            form.setError(field as (typeof FIELDS)[number], { message })
        }
      } else {
        form.setError('root', { message: error instanceof ApiError ? error.message : 'Saving failed' })
      }
    }
  })

  // Picking a saved company fills in the company name if it is still empty.
  const companyField = form.register('company_id', {
    onChange: (event: { target: { value: string } }) => {
      const picked = companies.data?.items.find((c) => String(c.id) === event.target.value)
      if (picked && !form.getValues('company').trim()) form.setValue('company', picked.name, { shouldValidate: true })
    },
  })

  return (
    <form onSubmit={submit} className="space-y-5" noValidate>
      {errors.root?.message && <ErrorMessage error={new ApiError(400, errors.root.message)} />}
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Company" error={errors.company?.message}>
          {(props) => <Input autoComplete="organization" {...props} {...form.register('company')} />}
        </Field>
        <Field label="Position" error={errors.position?.message}>
          {(props) => <Input autoComplete="organization-title" {...props} {...form.register('position')} />}
        </Field>
        <Field label="Location" error={errors.location?.message} hint='City, country or "Remote"'>
          {(props) => <Input {...props} {...form.register('location')} />}
        </Field>
        <Field label="Status" error={errors.status?.message}>
          {(props) => (
            <Select {...props} {...form.register('status')}>
              {APPLICATION_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field
          label="Linked company (optional)"
          error={errors.company_id?.message}
          hint={companies.data?.items.length === 0 ? 'Add companies on the Companies page to link them.' : undefined}
          className="sm:col-span-2"
        >
          {(props) => (
            <Select {...props} {...companyField} disabled={companies.isPending}>
              <option value="">Not linked</option>
              {companies.data?.items.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Notes" error={errors.notes?.message} className="sm:col-span-2">
          {(props) => <Textarea {...props} {...form.register('notes')} />}
        </Field>
      </div>
      <div className="flex justify-end gap-3">
        {onCancel && (
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" loading={isSubmitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
