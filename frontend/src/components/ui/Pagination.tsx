import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from './Button'

interface PaginationProps {
  total: number
  limit: number
  offset: number
  onChange: (offset: number) => void
}

export function Pagination({ total, limit, offset, onChange }: PaginationProps) {
  if (total === 0) return null
  const from = offset + 1
  const to = Math.min(offset + limit, total)
  return (
    <nav
      aria-label="Pagination"
      className="flex flex-col gap-3 border-t border-slate-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6"
    >
      <p className="text-sm text-slate-600">
        Showing <span className="font-medium">{from}</span>–<span className="font-medium">{to}</span> of{' '}
        <span className="font-medium">{total}</span>
      </p>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={offset === 0}
          onClick={() => onChange(Math.max(0, offset - limit))}
        >
          <ChevronLeft className="size-4" aria-hidden /> Previous
        </Button>
        <Button variant="secondary" size="sm" disabled={to >= total} onClick={() => onChange(offset + limit)}>
          Next <ChevronRight className="size-4" aria-hidden />
        </Button>
      </div>
    </nav>
  )
}
