import { type KeyboardEvent, type ReactNode, useId, useRef } from 'react'

import { cn } from '@/lib/cn'

export interface TabItem<T extends string> {
  id: T
  label: ReactNode
}

/** Accessible tabs (WAI-ARIA pattern): arrow keys, Home and End move between tabs. */
export function Tabs<T extends string>({
  label,
  items,
  value,
  onChange,
  children,
}: {
  label: string
  items: readonly TabItem<T>[]
  value: T
  onChange: (value: T) => void
  children: ReactNode
}) {
  const base = useId()
  const refs = useRef<Record<string, HTMLButtonElement | null>>({})

  function onKeyDown(event: KeyboardEvent) {
    const index = items.findIndex((item) => item.id === value)
    const next =
      event.key === 'ArrowRight'
        ? (index + 1) % items.length
        : event.key === 'ArrowLeft'
          ? (index - 1 + items.length) % items.length
          : event.key === 'Home'
            ? 0
            : event.key === 'End'
              ? items.length - 1
              : -1
    if (next < 0) return
    event.preventDefault()
    const target = items[next]!
    onChange(target.id)
    refs.current[target.id]?.focus()
  }

  return (
    <div>
      <div
        role="tablist"
        aria-label={label}
        className="-mx-1 flex gap-1 overflow-x-auto border-b border-slate-200 px-1"
      >
        {items.map((item) => {
          const selected = item.id === value
          return (
            <button
              key={item.id}
              ref={(node) => {
                refs.current[item.id] = node
              }}
              type="button"
              role="tab"
              id={`${base}-tab-${item.id}`}
              aria-selected={selected}
              aria-controls={`${base}-panel`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(item.id)}
              onKeyDown={onKeyDown}
              className={cn(
                '-mb-px flex shrink-0 items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium whitespace-nowrap',
                selected
                  ? 'border-brand-600 text-brand-700'
                  : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700',
              )}
            >
              {item.label}
            </button>
          )
        })}
      </div>
      <div
        role="tabpanel"
        id={`${base}-panel`}
        aria-labelledby={`${base}-tab-${value}`}
        tabIndex={0}
        className="pt-5 focus:outline-none"
      >
        {children}
      </div>
    </div>
  )
}
