/**
 * Access-token storage.
 *
 * The API issues short-lived bearer tokens (60 minutes by default). The token is
 * kept in localStorage so a page refresh keeps you signed in; it is removed on
 * logout, on any 401 response, and as soon as it expires.
 */

const KEY = 'careerops.token'

type Listener = () => void
const listeners = new Set<Listener>()

function decodeExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]!.replace(/-/g, '+').replace(/_/g, '/')))
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

export function getToken(): string | null {
  let token: string | null = null
  try {
    token = localStorage.getItem(KEY)
  } catch {
    return null
  }
  if (!token) return null
  const expiry = decodeExpiry(token)
  if (expiry === null || expiry <= Date.now()) {
    clearToken()
    return null
  }
  return token
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(KEY, token)
  } catch {
    // Storage unavailable (e.g. private mode): the session lasts until reload.
  }
  listeners.forEach((listener) => listener())
}

export function clearToken(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    // ignore
  }
  listeners.forEach((listener) => listener())
}

export function onTokenChange(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
