import { Link } from 'react-router'

import { buttonClasses } from '@/components/ui/buttonStyles'

export function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="mt-2 text-2xl font-semibold text-slate-900">Page not found</h1>
      <p className="mt-2 text-sm text-slate-500">The page you are looking for doesn't exist or was moved.</p>
      <Link to="/" className={buttonClasses('primary', 'md', 'mt-6')}>
        Back to home
      </Link>
    </div>
  )
}
