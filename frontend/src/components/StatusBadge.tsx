import type { ApplicationStatus } from '@/api/types'
import { cn } from '@/lib/cn'

const styles: Record<ApplicationStatus, string> = {
  Applied: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  Screening: 'bg-violet-50 text-violet-700 ring-violet-600/20',
  Interview: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  Offer: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  Rejected: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  Withdrawn: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}

export function StatusBadge({ status, className }: { status: ApplicationStatus; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset',
        styles[status],
        className,
      )}
    >
      {status}
    </span>
  )
}
