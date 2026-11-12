import { Building2, Globe, MapPin, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'

import { useCompanies, useCreateCompany } from '@/api/hooks'
import type { CompanySort } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/Button'
import { Card, PageHeader } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Dialogs'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input, Select } from '@/components/ui/Field'
import { Pagination } from '@/components/ui/Pagination'
import { Spinner } from '@/components/ui/Spinner'
import { useDebouncedValue } from '@/lib/useDebouncedValue'

import { CompanyForm } from './CompanyForm'

const PAGE_SIZE = 24

export function CompaniesPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<CompanySort>('name')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const q = useDebouncedValue(search.trim())
  const { data, error, isPending, refetch } = useCompanies({ q: q || undefined, sort, limit: PAGE_SIZE, offset })
  const create = useCreateCompany()

  return (
    <>
      <PageHeader
        title="Companies"
        description="Research notes on the companies you are targeting."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden /> New company
          </Button>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400"
            aria-hidden
          />
          <Input
            type="search"
            placeholder="Search name, industry or location"
            aria-label="Search companies"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setOffset(0)
            }}
            className="pl-9"
          />
        </div>
        <Select
          aria-label="Sort companies"
          value={sort}
          onChange={(event) => {
            setSort(event.target.value as CompanySort)
            setOffset(0)
          }}
          className="sm:w-48"
        >
          <option value="name">Name A–Z</option>
          <option value="-name">Name Z–A</option>
          <option value="-created_at">Recently added</option>
        </Select>
      </div>

      {error ? (
        <ErrorMessage error={error} onRetry={() => refetch()} />
      ) : isPending ? (
        <div className="flex justify-center p-12 text-brand-600">
          <Spinner label="Loading companies" className="size-6" />
        </div>
      ) : data.items.length === 0 ? (
        <Card>
          {q ? (
            <EmptyState icon={Search} title="No matches" description="Try a different search." />
          ) : (
            <EmptyState
              icon={Building2}
              title="No companies yet"
              description="Save companies to keep research notes and link them to your applications."
              action={
                <Button onClick={() => setCreating(true)}>
                  <Plus className="size-4" aria-hidden /> Add a company
                </Button>
              }
            />
          )}
        </Card>
      ) : (
        <>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((company) => (
              <li key={company.id}>
                <Link
                  to={`/companies/${company.id}`}
                  className="block h-full rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200 transition hover:ring-brand-300"
                >
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="font-semibold text-slate-900">{company.name}</h2>
                    <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                      {company.application_count} {company.application_count === 1 ? 'application' : 'applications'}
                    </span>
                  </div>
                  {company.industry && <p className="mt-1 text-sm text-slate-600">{company.industry}</p>}
                  <div className="mt-3 space-y-1 text-xs text-slate-500">
                    {company.location && (
                      <p className="flex items-center gap-1.5">
                        <MapPin className="size-3.5" aria-hidden /> {company.location}
                      </p>
                    )}
                    {company.website && (
                      <p className="flex items-center gap-1.5 truncate">
                        <Globe className="size-3.5" aria-hidden /> {company.website.replace(/^https?:\/\//, '')}
                      </p>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
          <Card className="mt-4">
            <Pagination total={data.total} limit={PAGE_SIZE} offset={offset} onChange={setOffset} />
          </Card>
        </>
      )}

      <Modal open={creating} onOpenChange={setCreating} title="New company">
        <CompanyForm
          submitLabel="Save company"
          onCancel={() => setCreating(false)}
          onSubmit={async (input) => {
            const company = await create.mutateAsync(input)
            toast.success(`${company.name} saved`)
            setCreating(false)
            navigate(`/companies/${company.id}`)
          }}
        />
      </Modal>
    </>
  )
}
