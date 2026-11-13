import { ApiError } from '@/api/client'

/** A message that is safe and useful to show the user. */
export function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong. Please try again.'
}
