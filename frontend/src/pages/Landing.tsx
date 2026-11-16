import { Building2, ClipboardList, LayoutDashboard, Lock, Search, Sparkles } from 'lucide-react'
import { Link } from 'react-router'

import { useAuth } from '@/auth/context'
import { Logo } from '@/components/Logo'
import { StatusBadge } from '@/components/StatusBadge'
import { buttonClasses } from '@/components/ui/buttonStyles'

const FEATURES = [
  {
    icon: ClipboardList,
    title: 'Every application in one place',
    text: 'Track company, role, location, notes and status from Applied to Offer.',
  },
  {
    icon: Search,
    title: 'Find anything fast',
    text: 'Search, filter by status, sort and page through your applications.',
  },
  {
    icon: Building2,
    title: 'Company research',
    text: 'Keep notes on the companies you target and see every application to each one.',
  },
  {
    icon: Lock,
    title: 'Private by design',
    text: 'Your data belongs to your account only. Passwords are hashed with Argon2.',
  },
]

const ROADMAP = [
  { icon: LayoutDashboard, title: 'Dashboard, Kanban board and interview calendar' },
  { icon: Sparkles, title: 'AI career assistant for job matching and interview prep' },
]

export function Landing() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
        <Logo />
        <nav aria-label="Account" className="flex items-center gap-2">
          {user ? (
            <Link to="/applications" className={buttonClasses('primary')}>
              Open CareerOps
            </Link>
          ) : (
            <>
              <Link to="/login" className={buttonClasses('ghost')}>
                Sign in
              </Link>
              <Link to="/register" className={buttonClasses('primary')}>
                Get started
              </Link>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div
            className="absolute inset-x-0 -top-40 -z-10 h-[32rem] bg-gradient-to-b from-brand-50 to-white"
            aria-hidden
          />
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 pt-16 pb-20 sm:px-6 lg:grid-cols-2 lg:pt-24">
            <div>
              <p className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700 ring-1 ring-brand-200">
                Your job search, organised
              </p>
              <h1 className="mt-6 text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
                Stay on top of every job application
              </h1>
              <p className="mt-6 text-lg text-slate-600">
                CareerOps keeps your applications, companies and progress in one secure place, so you always know what
                to follow up on next.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link to={user ? '/applications' : '/register'} className={buttonClasses('primary', 'lg')}>
                  {user ? 'Go to your applications' : 'Create a free account'}
                </Link>
                {!user && (
                  <Link to="/login" className={buttonClasses('secondary', 'lg')}>
                    Sign in
                  </Link>
                )}
              </div>
            </div>

            <div className="rounded-2xl bg-white p-4 shadow-xl ring-1 ring-slate-200" aria-hidden>
              <div className="flex items-center justify-between border-b border-slate-100 px-2 pb-3">
                <span className="text-sm font-semibold text-slate-900">Applications</span>
                <span className="text-xs text-slate-500">Example</span>
              </div>
              <ul className="divide-y divide-slate-100">
                {(
                  [
                    ['Northwind Labs', 'Backend Engineer', 'Interview'],
                    ['Blue Harbor', 'Python Developer', 'Screening'],
                    ['Kestrel Cloud', 'Platform Engineer', 'Applied'],
                    ['Orbit Health', 'API Engineer', 'Offer'],
                  ] as const
                ).map(([company, role, status]) => (
                  <li key={company} className="flex items-center justify-between px-2 py-3">
                    <div>
                      <p className="text-sm font-medium text-slate-900">{company}</p>
                      <p className="text-xs text-slate-500">{role}</p>
                    </div>
                    <StatusBadge status={status} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6" aria-labelledby="features">
          <h2 id="features" className="text-2xl font-semibold tracking-tight text-slate-900">
            What you can do today
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <div key={title} className="rounded-xl p-6 ring-1 ring-slate-200">
                <Icon className="size-6 text-brand-600" aria-hidden />
                <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
                <p className="mt-2 text-sm text-slate-600">{text}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6" aria-labelledby="roadmap">
          <div className="rounded-2xl bg-slate-50 p-8 ring-1 ring-slate-200">
            <h2 id="roadmap" className="text-lg font-semibold text-slate-900">
              Coming next
            </h2>
            <ul className="mt-4 grid gap-4 sm:grid-cols-2">
              {ROADMAP.map(({ icon: Icon, title }) => (
                <li key={title} className="flex items-center gap-3 text-sm text-slate-700">
                  <Icon className="size-5 text-slate-400" aria-hidden />
                  {title}
                </li>
              ))}
            </ul>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-8 text-center text-sm text-slate-500">
        CareerOps — a portfolio project built with FastAPI, PostgreSQL and React.
      </footer>
    </div>
  )
}
