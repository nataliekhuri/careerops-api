import { ArrowLeft, Building2, CalendarPlus, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { ApiError } from '@/api/client'
import {
  useApplication,
  useCreateApplication,
  useCreateInterview,
  useDeleteApplication,
  useInterviews,
  useUpdateApplication,
} from '@/api/hooks'
import { APPLICATION_STATUSES, type ApplicationStatus } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { errorText } from '@/lib/errors'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/Button'
import { Card, PageHeader } from '@/components/ui/Card'
import { ConfirmDialog, Modal } from '@/components/ui/Dialogs'
import { Select } from '@/components/ui/Field'
import { FullPageSpinner, Spinner } from '@/components/ui/Spinner'
import { formatDateTime } from '@/lib/format'
import { InterviewForm } from '@/pages/interviews/InterviewForm'
import { label as interviewLabel } from '@/pages/interviews/labels'
import { NotFound } from '@/pages/NotFound'

import { ApplicationForm } from './ApplicationForm'

function BackLink() {
  return (
    <Link
      to="/applications"
      className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
    >
      <ArrowLeft className="size-4" aria-hidden /> All applications
    </Link>
  )
}

export function NewApplicationPage() {
  const navigate = useNavigate()
  const create = useCreateApplication()
  return (
    <>
      <BackLink />
      <PageHeader title="New application" description="Record a job you have applied to." />
      <Card className="p-6">
        <ApplicationForm
          submitLabel="Save application"
          onCancel={() => navigate('/applications')}
          onSubmit={async (input) => {
            const application = await create.mutateAsync(input)
            toast.success('Application saved')
            navigate(`/applications/${application.id}`)
          }}
        />
      </Card>
    </>
  )
}

export function ApplicationDetailPage() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const { data: application, error, isPending, refetch } = useApplication(id)
  const update = useUpdateApplication(id)
  const remove = useDeleteApplication()
  const [editing, setEditing] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  if (!Number.isInteger(id) || id <= 0 || (error instanceof ApiError && error.status === 404)) return <NotFound />
  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />
  if (isPending) return <FullPageSpinner label="Loading application" />

  async function changeStatus(status: ApplicationStatus) {
    try {
      await update.mutateAsync({ status })
      toast.success(`Status changed to ${status}`)
    } catch (err) {
      toast.error(errorText(err))
    }
  }

  async function deleteApplication() {
    try {
      await remove.mutateAsync(id)
      toast.success('Application deleted')
      navigate('/applications')
    } catch (err) {
      toast.error(errorText(err))
      setConfirmDelete(false)
    }
  }

  return (
    <>
      <BackLink />
      <PageHeader
        title={application.position}
        description={
          <span className="flex flex-wrap items-center gap-2">
            {application.company} · {application.location} <StatusBadge status={application.status} />
          </span>
        }
        actions={
          !editing && (
            <>
              <Button variant="secondary" onClick={() => setEditing(true)}>
                <Pencil className="size-4" aria-hidden /> Edit
              </Button>
              <Button variant="danger" onClick={() => setConfirmDelete(true)}>
                <Trash2 className="size-4" aria-hidden /> Delete
              </Button>
            </>
          )
        }
      />

      {editing ? (
        <Card className="p-6">
          <ApplicationForm
            initial={application}
            submitLabel="Save changes"
            onCancel={() => setEditing(false)}
            onSubmit={async (input) => {
              await update.mutateAsync(input)
              toast.success('Changes saved')
              setEditing(false)
            }}
          />
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="p-6 lg:col-span-2">
            <h2 className="text-sm font-semibold text-slate-900">Notes</h2>
            {application.notes ? (
              <p className="mt-3 text-sm whitespace-pre-wrap text-slate-700">{application.notes}</p>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No notes yet. Use Edit to add some.</p>
            )}
          </Card>
          <Card className="space-y-5 p-6">
            <div>
              <label htmlFor="quick-status" className="text-sm font-semibold text-slate-900">
                Status
              </label>
              <Select
                id="quick-status"
                className="mt-2"
                value={application.status}
                disabled={update.isPending}
                onChange={(event) => changeStatus(event.target.value as ApplicationStatus)}
              >
                {APPLICATION_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </Select>
            </div>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-slate-500">Linked company</dt>
                <dd className="mt-0.5">
                  {application.company_id ? (
                    <Link
                      to={`/companies/${application.company_id}`}
                      className="inline-flex items-center gap-1 font-medium text-brand-600 hover:text-brand-700"
                    >
                      <Building2 className="size-4" aria-hidden /> View company
                    </Link>
                  ) : (
                    <span className="text-slate-700">Not linked</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Created</dt>
                <dd className="mt-0.5 text-slate-700">{formatDateTime(application.created_at)}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Last updated</dt>
                <dd className="mt-0.5 text-slate-700">{formatDateTime(application.updated_at)}</dd>
              </div>
            </dl>
          </Card>
        </div>
      )}

      {!editing && <ApplicationInterviews applicationId={application.id} />}

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete this application?"
        description={`"${application.position}" at ${application.company} and its interviews will be permanently deleted.`}
        confirmLabel="Delete application"
        loading={remove.isPending}
        onConfirm={deleteApplication}
      />
    </>
  )
}

function ApplicationInterviews({ applicationId }: { applicationId: number }) {
  const { data, error, isPending } = useInterviews({ application_id: applicationId, limit: 100 })
  const create = useCreateInterview()
  // The default date is captured when the dialog opens, not on every render.
  const [scheduling, setScheduling] = useState<Date | null>(null)

  return (
    <Card className="mt-6">
      <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
        <h2 className="text-sm font-semibold text-slate-900">Interviews</h2>
        <Button size="sm" variant="secondary" onClick={() => setScheduling(new Date())}>
          <CalendarPlus className="size-4" aria-hidden /> Schedule interview
        </Button>
      </div>
      {error ? (
        <div className="p-4">
          <ErrorMessage error={error} />
        </div>
      ) : isPending ? (
        <div className="flex justify-center p-6 text-brand-600">
          <Spinner label="Loading interviews" />
        </div>
      ) : data.items.length === 0 ? (
        <p className="px-6 py-6 text-sm text-slate-500">No interviews scheduled for this application yet.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {data.items.map((interview) => (
            <li key={interview.id} className="flex items-center justify-between gap-4 px-6 py-3 text-sm">
              <span>
                <span className="font-medium text-slate-900">{formatDateTime(interview.scheduled_at)}</span>
                <span className="text-slate-500"> · {interviewLabel(interview.interview_type)}</span>
              </span>
              <span className="text-xs text-slate-500">{interviewLabel(interview.outcome)}</span>
            </li>
          ))}
        </ul>
      )}
      <Modal
        open={scheduling !== null}
        onOpenChange={(open) => !open && setScheduling(null)}
        title="Schedule interview"
      >
        <InterviewForm
          defaultApplicationId={applicationId}
          defaultDate={scheduling ?? undefined}
          submitLabel="Schedule interview"
          onCancel={() => setScheduling(null)}
          onCreate={async (input) => {
            await create.mutateAsync(input)
            toast.success('Interview scheduled')
            setScheduling(null)
          }}
        />
      </Modal>
    </Card>
  )
}
