import { CalendarClock, ClipboardList, KanbanSquare, Percent, Plus, Target } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { useDashboardStats } from '@/api/hooks'
import { APPLICATION_STATUSES, type ApplicationStatus, type DashboardStats } from '@/api/types'
import { useAuth } from '@/auth/context'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Card, PageHeader } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { FullPageSpinner } from '@/components/ui/Spinner'
import { formatDateTime } from '@/lib/format'

const BAR_COLORS: Record<ApplicationStatus, string> = {
  Applied: 'bg-sky-500',
  Screening: 'bg-violet-500',
  Interview: 'bg-amber-500',
  Offer: 'bg-emerald-500',
  Rejected: 'bg-rose-500',
  Withdrawn: 'bg-slate-400',
}

const weekLabel = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' })

function StatCard({ label, value, hint, icon }: { label: string; value: ReactNode; hint?: string; icon: ReactNode }) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <span className="rounded-lg bg-brand-50 p-2 text-brand-600" aria-hidden>
          {icon}
        </span>
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </Card>
  )
}

function WeeklyChart({ weeks }: { weeks: DashboardStats['applications_per_week'] }) {
  const data = weeks.map((week) => ({
    label: weekLabel.format(new Date(`${week.week_start}T00:00:00Z`)),
    count: week.count,
  }))
  const total = data.reduce((sum, week) => sum + week.count, 0)
  return (
    <figure>
      <figcaption className="sr-only">Applications per week for the last 12 weeks: {total} in total.</figcaption>
      <div className="h-64" aria-hidden>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: '#eef2ff' }}
              formatter={(value) => [value, 'Applications']}
              contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0' }}
            />
            <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={36} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <thead>
          <tr>
            <th>Week starting</th>
            <th>Applications</th>
          </tr>
        </thead>
        <tbody>
          {data.map((week) => (
            <tr key={week.label}>
              <td>{week.label}</td>
              <td>{week.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}

function StatusBreakdown({ byStatus, total }: { byStatus: Record<string, number>; total: number }) {
  return (
    <ul className="space-y-3">
      {APPLICATION_STATUSES.map((status) => {
        const count = byStatus[status] ?? 0
        const percent = total ? Math.round((count / total) * 100) : 0
        return (
          <li key={status}>
            <div className="flex items-center justify-between text-sm">
              <Link
                to={`/applications?status=${status}`}
                className="text-slate-700 hover:text-brand-700 hover:underline"
              >
                {status}
              </Link>
              <span className="text-slate-500">
                {count} <span className="sr-only">applications</span>
              </span>
            </div>
            <div className="mt-1 h-2 rounded-full bg-slate-100" aria-hidden>
              <div className={`h-2 rounded-full ${BAR_COLORS[status]}`} style={{ width: `${percent}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, error, isPending, refetch } = useDashboardStats()
  const firstName = user?.full_name.split(' ')[0]

  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />
  if (isPending) return <FullPageSpinner label="Loading your dashboard" />

  const header = (
    <PageHeader
      title={firstName ? `Welcome back, ${firstName}` : 'Dashboard'}
      description="Your job search at a glance."
      actions={
        <Link to="/applications/new" className={buttonClasses('primary')}>
          <Plus className="size-4" aria-hidden /> New application
        </Link>
      }
    />
  )

  if (stats.total_applications === 0) {
    return (
      <>
        {header}
        <Card>
          <EmptyState
            icon={ClipboardList}
            title="Your dashboard fills up as you apply"
            description="Add your first application to see your progress, response rate and weekly activity here."
            action={
              <Link to="/applications/new" className={buttonClasses('primary')}>
                <Plus className="size-4" aria-hidden /> Add an application
              </Link>
            }
          />
        </Card>
      </>
    )
  }

  return (
    <>
      {header}

      <section aria-label="Key figures" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Applications"
          value={stats.total_applications}
          hint={`${stats.active_applications} still active`}
          icon={<ClipboardList className="size-4" />}
        />
        <StatCard
          label="Response rate"
          value={`${stats.rates.response_rate}%`}
          hint="Heard back (excluding withdrawn)"
          icon={<Percent className="size-4" />}
        />
        <StatCard
          label="Interview rate"
          value={`${stats.rates.interview_rate}%`}
          hint={`Offer rate ${stats.rates.offer_rate}%`}
          icon={<Target className="size-4" />}
        />
        <StatCard
          label="Upcoming interviews"
          value={stats.upcoming_interviews_count}
          hint={`${stats.total_interviews} scheduled in total`}
          icon={<CalendarClock className="size-4" />}
        />
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-900">Applications per week</h2>
          <p className="text-xs text-slate-500">Last 12 weeks</p>
          <div className="mt-4">
            <WeeklyChart weeks={stats.applications_per_week} />
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">Pipeline</h2>
            <Link
              to="/board"
              className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700"
            >
              <KanbanSquare className="size-3.5" aria-hidden /> Open board
            </Link>
          </div>
          <div className="mt-4">
            <StatusBreakdown byStatus={stats.by_status} total={stats.total_applications} />
          </div>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <h2 className="text-sm font-semibold text-slate-900">Upcoming interviews</h2>
            <Link to="/interviews" className="text-xs font-medium text-brand-600 hover:text-brand-700">
              View calendar
            </Link>
          </div>
          {stats.upcoming_interviews.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-slate-500">
              No interviews scheduled. Good luck with the applications!
            </p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {stats.upcoming_interviews.map((interview) => (
                <li key={interview.id}>
                  <Link
                    to={`/applications/${interview.application.id}`}
                    className="flex items-center justify-between gap-4 px-6 py-4 hover:bg-slate-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-900">
                        {interview.application.company} · {interview.application.position}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDateTime(interview.scheduled_at)} ·{' '}
                        <span className="capitalize">{interview.interview_type}</span>
                      </p>
                    </div>
                    <StatusBadge status={interview.application.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card>
          <h2 className="border-b border-slate-200 px-6 py-4 text-sm font-semibold text-slate-900">Top companies</h2>
          <ol className="divide-y divide-slate-100">
            {stats.top_companies.map(({ company, count }, index) => (
              <li key={company} className="flex items-center justify-between px-6 py-3 text-sm">
                <span className="flex items-center gap-3">
                  <span className="w-4 text-xs text-slate-400">{index + 1}</span>
                  <Link
                    to={`/applications?q=${encodeURIComponent(company)}`}
                    className="font-medium text-slate-900 hover:text-brand-700 hover:underline"
                  >
                    {company}
                  </Link>
                </span>
                <span className="text-slate-500">
                  {count} {count === 1 ? 'application' : 'applications'}
                </span>
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </>
  )
}
