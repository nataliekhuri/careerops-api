import {
  DndContext,
  type DragEndEvent,
  DragOverlay,
  type DragStartEvent,
  type KeyboardCoordinateGetter,
  KeyboardSensor,
  PointerSensor,
  TouchSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, KanbanSquare, Plus } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'

import { useBoardApplications, useMoveApplication } from '@/api/hooks'
import { APPLICATION_STATUSES, type Application, type ApplicationStatus } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Card, PageHeader } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { FullPageSpinner } from '@/components/ui/Spinner'
import { cn } from '@/lib/cn'
import { errorText } from '@/lib/errors'
import { formatDate } from '@/lib/format'

const COLUMN_ACCENT: Record<ApplicationStatus, string> = {
  Applied: 'border-t-sky-500',
  Screening: 'border-t-violet-500',
  Interview: 'border-t-amber-500',
  Offer: 'border-t-emerald-500',
  Rejected: 'border-t-rose-500',
  Withdrawn: 'border-t-slate-400',
}

/**
 * Keyboard dragging: Left/Right jump a whole column (the default moves 25px per press,
 * which never reaches the next column). Up/Down do nothing because order is not stored.
 */
const columnKeyboardCoordinates: KeyboardCoordinateGetter = (event, { context, currentCoordinates }) => {
  const step = event.code === 'ArrowRight' ? 1 : event.code === 'ArrowLeft' ? -1 : 0
  if (step === 0) return undefined
  event.preventDefault()
  const from = (context.over?.id ?? (context.active?.data.current?.application as Application | undefined)?.status) as
    ApplicationStatus | undefined
  const index = from ? APPLICATION_STATUSES.indexOf(from) : -1
  const target = APPLICATION_STATUSES[index + step]
  const rect = target && context.droppableRects.get(target)
  if (!rect) return currentCoordinates
  const width = context.collisionRect?.width ?? 0
  return { x: rect.left + (rect.width - width) / 2, y: currentCoordinates.y }
}

function CardBody({ application }: { application: Application }) {
  return (
    <>
      <p className="truncate font-medium text-slate-900">{application.company}</p>
      <p className="truncate text-sm text-slate-600">{application.position}</p>
      <p className="mt-1 text-xs text-slate-500">
        {application.location} · {formatDate(application.updated_at)}
      </p>
    </>
  )
}

function BoardCard({
  application,
  onMove,
}: {
  application: Application
  onMove: (application: Application, status: ApplicationStatus) => void
}) {
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, isDragging } = useDraggable({
    id: application.id,
    data: { application },
  })
  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform) }}
      className={cn('rounded-lg bg-white p-3 shadow-sm ring-1 ring-slate-200', isDragging && 'opacity-40')}
    >
      <div className="flex items-start gap-2">
        <button
          ref={setActivatorNodeRef}
          type="button"
          className="mt-0.5 cursor-grab touch-none rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 active:cursor-grabbing"
          aria-label={`Drag ${application.position} at ${application.company}`}
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-4" aria-hidden />
        </button>
        <Link to={`/applications/${application.id}`} className="min-w-0 flex-1 rounded hover:text-brand-700">
          <CardBody application={application} />
        </Link>
      </div>
      <label className="mt-2 flex items-center gap-2 text-xs text-slate-500">
        <span className="whitespace-nowrap">Move to</span>
        <select
          className="h-7 flex-1 rounded-md border-0 bg-slate-50 px-2 text-xs text-slate-700 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-brand-500"
          value={application.status}
          onChange={(event) => onMove(application, event.target.value as ApplicationStatus)}
          aria-label={`Move ${application.position} at ${application.company} to`}
        >
          {APPLICATION_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </label>
    </li>
  )
}

function Column({
  status,
  items,
  onMove,
}: {
  status: ApplicationStatus
  items: Application[]
  onMove: (application: Application, status: ApplicationStatus) => void
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status })
  return (
    <section
      ref={setNodeRef}
      aria-labelledby={`column-${status}`}
      className={cn(
        'flex w-72 shrink-0 flex-col rounded-xl border-t-4 bg-slate-100/70 p-3 transition-colors',
        COLUMN_ACCENT[status],
        isOver && 'bg-brand-50 ring-2 ring-brand-300',
      )}
    >
      <h2
        id={`column-${status}`}
        className="mb-3 flex items-center justify-between px-1 text-sm font-semibold text-slate-700"
      >
        {status}
        <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-slate-500 ring-1 ring-slate-200">
          {items.length}
        </span>
      </h2>
      <ul className="flex min-h-24 flex-1 flex-col gap-2">
        {items.map((application) => (
          <BoardCard key={application.id} application={application} onMove={onMove} />
        ))}
        {items.length === 0 && (
          <li className="rounded-lg border-2 border-dashed border-slate-200 p-4 text-center text-xs text-slate-400">
            Drop here
          </li>
        )}
      </ul>
    </section>
  )
}

export function BoardPage() {
  const { data, error, isPending, refetch } = useBoardApplications()
  const move = useMoveApplication()
  const [active, setActive] = useState<Application | null>(null)
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 150, tolerance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: columnKeyboardCoordinates }),
  )

  function moveTo(application: Application, status: ApplicationStatus) {
    if (application.status === status) return
    move.mutate(
      { id: application.id, status },
      {
        onSuccess: () => toast.success(`${application.company} moved to ${status}`),
        onError: (err) => toast.error(`Could not move ${application.company}: ${errorText(err)}`),
      },
    )
  }

  function onDragStart(event: DragStartEvent) {
    setActive((event.active.data.current?.application as Application | undefined) ?? null)
  }

  function onDragEnd(event: DragEndEvent) {
    setActive(null)
    const application = event.active.data.current?.application as Application | undefined
    const status = event.over?.id as ApplicationStatus | undefined
    if (application && status) moveTo(application, status)
  }

  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />
  if (isPending) return <FullPageSpinner label="Loading your board" />

  return (
    <>
      <PageHeader
        title="Board"
        description="Drag cards between columns (or use “Move to”) to update their status."
        actions={
          <Link to="/applications/new" className={buttonClasses('primary')}>
            <Plus className="size-4" aria-hidden /> New application
          </Link>
        }
      />
      {data.length === 0 ? (
        <Card>
          <EmptyState
            icon={KanbanSquare}
            title="Your board is empty"
            description="Add applications and move them through Applied, Interview and Offer here."
            action={
              <Link to="/applications/new" className={buttonClasses('primary')}>
                <Plus className="size-4" aria-hidden /> Add an application
              </Link>
            }
          />
        </Card>
      ) : (
        <DndContext
          sensors={sensors}
          onDragStart={onDragStart}
          onDragEnd={onDragEnd}
          onDragCancel={() => setActive(null)}
          accessibility={{
            announcements: {
              onDragStart: ({ active: item }) => `Picked up ${describe(item.data.current?.application)}.`,
              onDragOver: ({ over }) => (over ? `Over ${over.id}.` : 'Not over a column.'),
              onDragEnd: ({ over, active: item }) =>
                over ? `Moved ${describe(item.data.current?.application)} to ${over.id}.` : 'Move cancelled.',
              onDragCancel: () => 'Move cancelled.',
            },
          }}
        >
          <div className="-mx-4 overflow-x-auto px-4 pb-4 sm:-mx-6 sm:px-6">
            <div className="flex gap-4">
              {APPLICATION_STATUSES.map((status) => (
                <Column key={status} status={status} items={data.filter((a) => a.status === status)} onMove={moveTo} />
              ))}
            </div>
          </div>
          <DragOverlay>
            {active && (
              <div className="w-64 rotate-2 rounded-lg bg-white p-3 shadow-xl ring-2 ring-brand-400">
                <CardBody application={active} />
                <div className="mt-2">
                  <StatusBadge status={active.status} />
                </div>
              </div>
            )}
          </DragOverlay>
        </DndContext>
      )}
    </>
  )
}

function describe(application: unknown): string {
  const a = application as Application | undefined
  return a ? `${a.position} at ${a.company}` : 'application'
}
