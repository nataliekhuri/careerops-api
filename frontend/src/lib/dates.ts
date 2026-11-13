/** Small, dependency-free date helpers for the calendar (local time, weeks start on Monday). */

export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

export function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

export function addMonths(date: Date, months: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + months, 1)
}

export function addDays(date: Date, days: number): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days)
}

/** Monday of the week containing `date`. */
export function startOfWeek(date: Date): Date {
  const day = (date.getDay() + 6) % 7 // Monday = 0
  return addDays(startOfDay(date), -day)
}

export function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

/** The 6×7 grid of days shown for a month (always 42 days, Monday first). */
export function monthGrid(month: Date): Date[] {
  const first = startOfWeek(startOfMonth(month))
  return Array.from({ length: 42 }, (_, i) => addDays(first, i))
}

export function dayKey(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** Value for <input type="date"> / <input type="time"> in local time. */
export function toDateInput(date: Date): string {
  return dayKey(date)
}

export function toTimeInput(date: Date): string {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

/** Combine local date and time inputs into an ISO string with a time zone (UTC). */
export function localDateTimeToIso(date: string, time: string): string {
  const [year, month, day] = date.split('-').map(Number)
  const [hours, minutes] = time.split(':').map(Number)
  return new Date(year!, month! - 1, day!, hours!, minutes!).toISOString()
}

export const WEEKDAYS = Array.from({ length: 7 }, (_, i) =>
  new Intl.DateTimeFormat(undefined, { weekday: 'short' }).format(new Date(2024, 0, 1 + i)),
) // 2024-01-01 was a Monday
