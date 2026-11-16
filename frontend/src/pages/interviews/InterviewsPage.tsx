import { CalendarDays, ChevronLeft, ChevronRight, ExternalLink, MapPin, Pencil, Plus, Trash2, User } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'

import { useCreateInterview, useDeleteInterview, useInterviews, useUpdateInterview } from '@/api/hooks'
import type { Interview, InterviewOutcome } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/Button'
import { Card, PageHeader } from '@/components/ui/Card'
import { ConfirmDialog, Modal } from '@/components/ui/Dialogs'
import { Spinner } from '@/components/ui/Spinner'
import { cn } from '@/lib/cn'
import { addDays, addMonths, dayKey, isSameDay, monthGrid, startOfDay, startOfMonth, WEEKDAYS } from '@/lib/dates'
import { errorText } from '@/lib/errors'

import { InterviewForm } from './InterviewForm'
import { label } from './labels'

const monthTitle = new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' })
const dayTitle = new Intl.DateTimeFormat(undefined, { weekday: 'long', day: 'numeric', month: 'long' })
const timeFormat = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' })

const OUTCOME_STYLE: Record<InterviewOutcome, string> = {
  pending: 'bg-brand-50 text-brand-700 ring-brand-600/20',
  passed: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  failed: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  cancelled: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}

function timeRange(interview: Interview) {
  const start = new Date(interview.scheduled_at)
  const end = new Date(start.getTime() + interview.duration_minutes * 60_000)
  return `${timeFormat.format(start)}–${timeFormat.format(end)}`
}

function InterviewItem({
  interview,
  onEdit,
  onDelete,
}: {
  interview: Interview
  onEdit: () => void
  onDelete: () => void
}) {
  const isLink = /^https?:\/\//i.test(interview.location)
  return (
    <li className="rounded-lg p-4 ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-900">{timeRange(interview)}</p>
          <Link
            to={`/applications/${interview.application.id}`}
            className="block truncate text-sm text-slate-700 hover:text-brand-700 hover:underline"
          >
            {interview.application.company} · {interview.application.position}
          </Link>
        </div>
        <span
          className={cn(
            'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset',
            OUTCOME_STYLE[interview.outcome],
          )}
        >
          {label(interview.outcome)}
        </span>
      </div>
      <dl className="mt-2 space-y-1 text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <dt className="sr-only">Type</dt>
          <CalendarDays className="size-3.5" aria-hidden />
          <dd>{label(interview.interview_type)}</dd>
        </div>
        {interview.location && (
          <div className="flex items-center gap-1.5">
            <dt className="sr-only">Location</dt>
            {isLink ? <ExternalLink className="size-3.5" aria-hidden /> : <MapPin className="size-3.5" aria-hidden />}
            <dd className="truncate">
              {isLink ? (
                <a
                  href={interview.location}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 hover:underline"
                >
                  Join meeting<span className="sr-only"> (opens in a new tab)</span>
                </a>
              ) : (
                interview.location
              )}
            </dd>
          </div>
        )}
        {interview.interviewer && (
          <div className="flex items-center gap-1.5">
            <dt className="sr-only">Interviewer</dt>
            <User className="size-3.5" aria-hidden />
            <dd className="truncate">{interview.interviewer}</dd>
          </div>
        )}
      </dl>
      {interview.notes && <p className="mt-2 text-xs whitespace-pre-wrap text-slate-600">{interview.notes}</p>}
      <div className="mt-3 flex gap-2">
        <Button size="sm" variant="secondary" onClick={onEdit}>
          <Pencil className="size-3.5" aria-hidden /> Edit
        </Button>
        <Button size="sm" variant="ghost" onClick={onDelete}>
          <Trash2 className="size-3.5" aria-hidden /> Delete
        </Button>
      </div>
    </li>
  )
}

export function InterviewsPage() {
  const [today] = useState(() => startOfDay(new Date()))
  const [month, setMonth] = useState(() => startOfMonth(today))
  const [selected, setSelected] = useState(today)
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<Interview | null>(null)
  const [deleting, setDeleting] = useState<Interview | null>(null)

  const days = useMemo(() => monthGrid(month), [month])
  const { data, error, isPending, isFetching, refetch } = useInterviews({
    start: days[0]!.toISOString(),
    end: addDays(days[days.length - 1]!, 1).toISOString(),
    limit: 500,
  })
  const create = useCreateInterview()
  const update = useUpdateInterview()
  const remove = useDeleteInterview()

  const byDay = useMemo(() => {
    const map = new Map<string, Interview[]>()
    for (const interview of data?.items ?? []) {
      const key = dayKey(new Date(interview.scheduled_at))
      map.set(key, [...(map.get(key) ?? []), interview])
    }
    return map
  }, [data])
  const selectedItems = byDay.get(dayKey(selected)) ?? []

  function goTo(next: Date) {
    setMonth(startOfMonth(next))
    setSelected(startOfDay(next))
  }

  return (
    <>
      <PageHeader
        title="Interviews"
        description="Your interview schedule. Times are shown in your time zone."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden /> Schedule interview
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="p-4 sm:p-6 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-slate-900" aria-live="polite">
              {monthTitle.format(month)}
              {isFetching && <Spinner className="ml-2 inline size-4 text-brand-600" label="Loading interviews" />}
            </h2>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setMonth(addMonths(month, -1))}
                aria-label="Previous month"
              >
                <ChevronLeft className="size-4" aria-hidden />
              </Button>
              <Button variant="secondary" size="sm" onClick={() => goTo(today)}>
                Today
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setMonth(addMonths(month, 1))} aria-label="Next month">
                <ChevronRight className="size-4" aria-hidden />
              </Button>
            </div>
          </div>

          {error ? (
            <ErrorMessage error={error} onRetry={() => refetch()} />
          ) : (
            <table className="w-full table-fixed border-collapse" aria-busy={isPending}>
              <caption className="sr-only">Interview calendar for {monthTitle.format(month)}</caption>
              <thead>
                <tr>
                  {WEEKDAYS.map((weekday) => (
                    <th key={weekday} scope="col" className="pb-2 text-center text-xs font-medium text-slate-500">
                      {weekday}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 6 }, (_, week) => (
                  <tr key={week}>
                    {days.slice(week * 7, week * 7 + 7).map((day) => {
                      const items = byDay.get(dayKey(day)) ?? []
                      const inMonth = day.getMonth() === month.getMonth()
                      const isSelected = isSameDay(day, selected)
                      return (
                        <td key={dayKey(day)} className="border border-slate-200 p-0">
                          <button
                            type="button"
                            onClick={() => setSelected(day)}
                            aria-pressed={isSelected}
                            aria-label={`${dayTitle.format(day)}, ${items.length} ${items.length === 1 ? 'interview' : 'interviews'}`}
                            className={cn(
                              'flex h-14 w-full flex-col items-start gap-1 bg-white p-1.5 text-left text-xs sm:h-24',
                              !inMonth && 'bg-slate-50 text-slate-400',
                              isSelected && 'ring-2 ring-brand-500 ring-inset',
                            )}
                          >
                            <span
                              className={cn(
                                'flex size-6 items-center justify-center rounded-full',
                                isSameDay(day, today) && 'bg-brand-600 font-semibold text-white',
                              )}
                            >
                              {day.getDate()}
                            </span>
                            {/* Dots on phones, titles on larger screens */}
                            <span className="flex gap-0.5 sm:hidden" aria-hidden>
                              {items.slice(0, 3).map((item) => (
                                <span key={item.id} className="size-1.5 rounded-full bg-brand-500" />
                              ))}
                            </span>
                            <span className="hidden w-full space-y-0.5 sm:block" aria-hidden>
                              {items.slice(0, 2).map((item) => (
                                <span
                                  key={item.id}
                                  className="block truncate rounded bg-brand-50 px-1 text-[11px] text-brand-700"
                                >
                                  {timeFormat.format(new Date(item.scheduled_at))} {item.application.company}
                                </span>
                              ))}
                              {items.length > 2 && (
                                <span className="block text-[11px] text-slate-500">+{items.length - 2} more</span>
                              )}
                            </span>
                          </button>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card className="p-4 sm:p-6">
          <h2 className="text-sm font-semibold text-slate-900">{dayTitle.format(selected)}</h2>
          {selectedItems.length === 0 ? (
            <div className="mt-6 text-center">
              <p className="text-sm text-slate-500">No interviews on this day.</p>
              <Button variant="secondary" size="sm" className="mt-3" onClick={() => setCreating(true)}>
                <Plus className="size-3.5" aria-hidden /> Schedule one
              </Button>
            </div>
          ) : (
            <ul className="mt-4 space-y-3" aria-label="Interviews on the selected day">
              {selectedItems.map((interview) => (
                <InterviewItem
                  key={interview.id}
                  interview={interview}
                  onEdit={() => setEditing(interview)}
                  onDelete={() => setDeleting(interview)}
                />
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Modal open={creating} onOpenChange={setCreating} title="Schedule interview">
        <InterviewForm
          defaultDate={selected}
          submitLabel="Schedule interview"
          onCancel={() => setCreating(false)}
          onCreate={async (input) => {
            const interview = await create.mutateAsync(input)
            toast.success(`Interview with ${interview.application.company} scheduled`)
            setCreating(false)
            goTo(new Date(interview.scheduled_at))
          }}
        />
      </Modal>

      <Modal open={editing !== null} onOpenChange={(open) => !open && setEditing(null)} title="Edit interview">
        {editing && (
          <InterviewForm
            initial={editing}
            submitLabel="Save changes"
            onCancel={() => setEditing(null)}
            onUpdate={async (body) => {
              await update.mutateAsync({ id: editing.id, body })
              toast.success('Interview updated')
              setEditing(null)
            }}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Delete this interview?"
        description={deleting ? `The interview with ${deleting.application.company} will be removed.` : ''}
        confirmLabel="Delete interview"
        loading={remove.isPending}
        onConfirm={async () => {
          if (!deleting) return
          try {
            await remove.mutateAsync(deleting.id)
            toast.success('Interview deleted')
          } catch (err) {
            toast.error(errorText(err))
          }
          setDeleting(null)
        }}
      />
    </>
  )
}
