import { ClipboardList, Plus, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import type { ApplicationQuery } from '@/api/hooks'
import { useApplications } from '@/api/hooks'
import { APPLICATION_STATUSES, type ApplicationSort, type ApplicationStatus } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Card, PageHeader } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input, Select } from '@/components/ui/Field'
import { Pagination } from '@/components/ui/Pagination'
import { Spinner } from '@/components/ui/Spinner'
import { formatDate } from '@/lib/format'
import { useDebouncedValue } from '@/lib/useDebouncedValue'

const PAGE_SIZE = 20

const SORTS: { value: ApplicationSort; label: string }[] = [
  { value: '-updated_at', label: 'Recently updated' },
  { value: '-created_at', label: 'Newest first' },
  { value: 'created_at', label: 'Oldest first' },
  { value: 'company', label: 'Company A–Z' },
  { value: '-company', label: 'Company Z–A' },
  { value: 'status', label: 'Status' },
]

function isStatus(value: string | null): value is ApplicationStatus {
  return APPLICATION_STATUSES.includes(value as ApplicationStatus)
}

export function ApplicationsPage() {
  // Filters live in the URL so views can be bookmarked and shared.
  const [params, setParams] = useSearchParams()
  const statusParam = params.get('status')
  const status = isStatus(statusParam) ? statusParam : undefined
  const sortParam = params.get('sort') as ApplicationSort | null
  const sort = SORTS.some((s) => s.value === sortParam) ? sortParam! : '-updated_at'
  const offset = Math.max(0, Number(params.get('offset')) || 0)

  const [search, setSearch] = useState(params.get('q') ?? '')
  const debouncedSearch = useDebouncedValue(search.trim())

  function update(changes: Record<string, string | undefined>) {
    setParams(
      (current) => {
        const next = new URLSearchParams(current)
        for (const [key, value] of Object.entries(changes)) {
          if (value) next.set(key, value)
          else next.delete(key)
        }
        if (!('offset' in changes)) next.delete('offset') // new filters start at page 1
        return next
      },
      { replace: true },
    )
  }

  // Push the (debounced) search box into the URL, starting again from page 1.
  useEffect(() => {
    setParams(
      (current) => {
        if ((current.get('q') ?? '') === debouncedSearch) return current
        const next = new URLSearchParams(current)
        if (debouncedSearch) next.set('q', debouncedSearch)
        else next.delete('q')
        next.delete('offset')
        return next
      },
      { replace: true },
    )
  }, [debouncedSearch, setParams])

  const query: ApplicationQuery = { sort, limit: PAGE_SIZE, offset }
  if (status) query.status = status
  if (params.get('q')) query.company = params.get('q')!
  const { data, error, isPending, isFetching, refetch } = useApplications(query)
  const filtered = Boolean(status || params.get('q'))

  return (
    <>
      <PageHeader
        title="Applications"
        description={data ? `${data.total} ${data.total === 1 ? 'application' : 'applications'}` : undefined}
        actions={
          <Link to="/applications/new" className={buttonClasses('primary')}>
            <Plus className="size-4" aria-hidden /> New application
          </Link>
        }
      />

      <Card>
        <div className="flex flex-col gap-3 border-b border-slate-200 p-4 sm:flex-row">
          <div className="relative flex-1">
            <Search
              className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400"
              aria-hidden
            />
            <Input
              type="search"
              placeholder="Search by company"
              aria-label="Search by company"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="pl-9"
            />
          </div>
          <Select
            aria-label="Filter by status"
            value={status ?? ''}
            onChange={(event) => update({ status: event.target.value || undefined })}
            className="sm:w-44"
          >
            <option value="">All statuses</option>
            {APPLICATION_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Sort"
            value={sort}
            onChange={(event) => update({ sort: event.target.value })}
            className="sm:w-48"
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </Select>
        </div>

        {error ? (
          <div className="p-4">
            <ErrorMessage error={error} onRetry={() => refetch()} />
          </div>
        ) : isPending ? (
          <div className="flex justify-center p-12 text-brand-600">
            <Spinner label="Loading applications" className="size-6" />
          </div>
        ) : data.items.length === 0 ? (
          filtered ? (
            <EmptyState icon={Search} title="No matches" description="Try a different search or status filter." />
          ) : (
            <EmptyState
              icon={ClipboardList}
              title="No applications yet"
              description="Add the jobs you have applied to and track their progress here."
              action={
                <Link to="/applications/new" className={buttonClasses('primary')}>
                  <Plus className="size-4" aria-hidden /> Add your first application
                </Link>
              }
            />
          )
        ) : (
          <div aria-busy={isFetching}>
            {/* Table on larger screens */}
            <table className="hidden w-full text-left text-sm md:table">
              <thead className="bg-slate-50 text-xs font-medium tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="px-6 py-3">
                    Company
                  </th>
                  <th scope="col" className="px-6 py-3">
                    Position
                  </th>
                  <th scope="col" className="px-6 py-3">
                    Location
                  </th>
                  <th scope="col" className="px-6 py-3">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3">
                    Updated
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((application) => (
                  <tr key={application.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium text-slate-900">
                      <Link to={`/applications/${application.id}`} className="hover:text-brand-700 hover:underline">
                        {application.company}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-slate-700">{application.position}</td>
                    <td className="px-6 py-4 text-slate-500">{application.location}</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={application.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-500">{formatDate(application.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Cards on phones */}
            <ul className="divide-y divide-slate-100 md:hidden">
              {data.items.map((application) => (
                <li key={application.id}>
                  <Link
                    to={`/applications/${application.id}`}
                    className="flex items-start justify-between gap-4 p-4 hover:bg-slate-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-900">{application.company}</p>
                      <p className="truncate text-sm text-slate-600">{application.position}</p>
                      <p className="text-xs text-slate-500">{application.location}</p>
                    </div>
                    <StatusBadge status={application.status} />
                  </Link>
                </li>
              ))}
            </ul>

            <Pagination
              total={data.total}
              limit={PAGE_SIZE}
              offset={offset}
              onChange={(next) => update({ offset: next ? String(next) : undefined })}
            />
          </div>
        )}
      </Card>
    </>
  )
}
