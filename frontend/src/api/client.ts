import createClient, { type Middleware } from 'openapi-fetch'

import { clearToken, getToken } from '@/auth/token'

import type { paths } from './schema'

export const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'

/** A field-level problem reported by the API (422 responses). */
export interface FieldError {
  field: string
  message: string
}

/** Any non-2xx API response, with a human-readable message. */
export class ApiError extends Error {
  readonly status: number
  readonly fieldErrors: FieldError[]

  constructor(status: number, message: string, fieldErrors: FieldError[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

const authMiddleware: Middleware = {
  onRequest({ request }) {
    const token = getToken()
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
  onResponse({ request, response }) {
    // A rejected token means the session is over: sign out everywhere.
    if (response.status === 401 && request.headers.has('Authorization')) clearToken()
    return response
  },
}

export const api = createClient<paths>({
  baseUrl: API_URL,
  // Look up fetch on every call (not once at import), so test tools and
  // browser extensions that wrap window.fetch are respected.
  fetch: (request) => globalThis.fetch(request),
})
api.use(authMiddleware)

interface ValidationIssue {
  loc?: (string | number)[]
  msg?: string
}

function toApiError(status: number, body: unknown): ApiError {
  const detail = (body as { detail?: unknown } | undefined)?.detail
  if (typeof detail === 'string') return new ApiError(status, detail)
  if (Array.isArray(detail)) {
    const fieldErrors = (detail as ValidationIssue[]).map((issue) => ({
      field: String(issue.loc?.[issue.loc.length - 1] ?? ''),
      message: (issue.msg ?? 'Invalid value').replace(/^Value error, /, ''),
    }))
    return new ApiError(status, fieldErrors[0]?.message ?? 'Please check the form', fieldErrors)
  }
  if (status >= 500) return new ApiError(status, 'Something went wrong on our side. Please try again.')
  return new ApiError(status, 'Request failed')
}

/** Return `data`, or throw an ApiError for any error response or network failure. */
export async function unwrap<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<{ data: T; response: Response }> {
  let result: Awaited<typeof request>
  try {
    result = await request
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection and try again.')
  }
  if (!result.response.ok) throw toApiError(result.response.status, result.error)
  return { data: result.data as T, response: result.response }
}

export function totalCount(response: Response): number {
  return Number(response.headers.get('X-Total-Count') ?? 0)
}
