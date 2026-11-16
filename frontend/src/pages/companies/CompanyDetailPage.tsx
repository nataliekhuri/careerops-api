import { ArrowLeft, ClipboardList, ExternalLink, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { ApiError } from '@/api/client'
import { useApplications, useCompany, useDeleteCompany, useUpdateCompany } from '@/api/hooks'
import { ErrorMessage } from '@/components/ErrorMessage'
import { errorText } from '@/lib/errors'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Card, PageHeader } from '@/components/ui/Card'
import { ConfirmDialog, Modal } from '@/components/ui/Dialogs'
import { EmptyState } from '@/components/ui/EmptyState'
import { FullPageSpinner, Spinner } from '@/components/ui/Spinner'
import { formatDate } from '@/lib/format'
import { NotFound } from '@/pages/NotFound'

import { CompanyForm } from './CompanyForm'

function LinkedApplications({ companyId }: { companyId: number }) {
  const { data, error, isPending } = useApplications({ company_id: companyId, sort: '-updated_at', limit: 100 })
  if (error) return <ErrorMessage error={error} />
  if (isPending)
    return (
      <div className="flex justify-center p-8 text-brand-600">
        <Spinner label="Loading applications" />
      </div>
    )
  if (data.items.length === 0)
    return (
      <EmptyState
        icon={ClipboardList}
        title="No linked applications"
        description="Link an application to this company from its edit form."
        action={
          <Link to="/applications/new" className={buttonClasses('secondary')}>
            <Plus className="size-4" aria-hidden /> New application
          </Link>
        }
      />
    )
  return (
    <ul className="divide-y divide-slate-100">
      {data.items.map((application) => (
        <li key={application.id}>
          <Link
            to={`/applications/${application.id}`}
            className="flex items-center justify-between gap-4 px-6 py-4 hover:bg-slate-50"
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-slate-900">{application.position}</p>
              <p className="text-xs text-slate-500">
                {application.location} · updated {formatDate(application.updated_at)}
              </p>
            </div>
            <StatusBadge status={application.status} />
          </Link>
        </li>
      ))}
    </ul>
  )
}

export function CompanyDetailPage() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const { data: company, error, isPending, refetch } = useCompany(id)
  const update = useUpdateCompany(id)
  const remove = useDeleteCompany()
  const [editing, setEditing] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  if (!Number.isInteger(id) || id <= 0 || (error instanceof ApiError && error.status === 404)) return <NotFound />
  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />
  if (isPending) return <FullPageSpinner label="Loading company" />

  return (
    <>
      <Link to="/companies" className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="size-4" aria-hidden /> All companies
      </Link>
      <PageHeader
        title={company.name}
        description={[company.industry, company.location].filter(Boolean).join(' · ') || undefined}
        actions={
          <>
            <Button variant="secondary" onClick={() => setEditing(true)}>
              <Pencil className="size-4" aria-hidden /> Edit
            </Button>
            <Button variant="danger" onClick={() => setConfirmDelete(true)}>
              <Trash2 className="size-4" aria-hidden /> Delete
            </Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="space-y-4 p-6">
          {company.website && (
            <a
              href={company.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700"
            >
              {company.website.replace(/^https?:\/\//, '')} <ExternalLink className="size-3.5" aria-hidden />
              <span className="sr-only">(opens in a new tab)</span>
            </a>
          )}
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Notes</h2>
            <p className="mt-2 text-sm whitespace-pre-wrap text-slate-700">
              {company.notes || <span className="text-slate-500">No notes yet.</span>}
            </p>
          </div>
        </Card>
        <Card className="lg:col-span-2">
          <h2 className="border-b border-slate-200 px-6 py-4 text-sm font-semibold text-slate-900">
            Applications ({company.application_count})
          </h2>
          <LinkedApplications companyId={company.id} />
        </Card>
      </div>

      <Modal open={editing} onOpenChange={setEditing} title="Edit company">
        <CompanyForm
          initial={company}
          submitLabel="Save changes"
          onCancel={() => setEditing(false)}
          onSubmit={async (input) => {
            await update.mutateAsync(input)
            toast.success('Company updated')
            setEditing(false)
          }}
        />
      </Modal>

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title={`Delete ${company.name}?`}
        description="The company and its notes are deleted. Linked applications are kept and simply unlinked."
        confirmLabel="Delete company"
        loading={remove.isPending}
        onConfirm={async () => {
          try {
            await remove.mutateAsync(company.id)
            toast.success('Company deleted')
            navigate('/companies')
          } catch (err) {
            toast.error(errorText(err))
            setConfirmDelete(false)
          }
        }}
      />
    </>
  )
}
