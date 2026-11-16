import { BriefcaseBusiness } from 'lucide-react'
import { Link } from 'react-router'

export function Logo({ to = '/' }: { to?: string }) {
  return (
    <Link to={to} className="flex items-center gap-2 rounded-md font-semibold text-slate-900">
      <span className="flex size-8 items-center justify-center rounded-lg bg-brand-600 text-white">
        <BriefcaseBusiness className="size-4" aria-hidden />
      </span>
      CareerOps
    </Link>
  )
}
