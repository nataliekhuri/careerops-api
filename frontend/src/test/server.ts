import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

import type { Application, Company, User } from '@/api/types'

export const API = 'http://localhost/api'

/** Network-level mock of the API. Tests add handlers with `server.use(...)`. */
export const server = setupServer()

/** A syntactically valid JWT that expires `seconds` from now (the frontend only reads `exp`). */
export function fakeToken(seconds = 3600): string {
  const encode = (value: object) => btoa(JSON.stringify(value)).replace(/=+$/, '')
  return `${encode({ alg: 'HS256' })}.${encode({ sub: '1', exp: Math.floor(Date.now() / 1000) + seconds })}.signature`
}

export const user: User = {
  id: 1,
  email: 'ann@example.com',
  full_name: 'Ann Example',
  created_at: '2026-11-01T10:00:00Z',
}

export function makeApplication(overrides: Partial<Application> = {}): Application {
  return {
    id: 1,
    company: 'Acme Corp',
    position: 'Backend Developer',
    location: 'Remote',
    status: 'Applied',
    notes: '',
    company_id: null,
    created_at: '2026-11-01T10:00:00Z',
    updated_at: '2026-11-02T10:00:00Z',
    ...overrides,
  }
}

export function makeCompany(overrides: Partial<Company> = {}): Company {
  return {
    id: 1,
    name: 'Acme Corp',
    website: 'https://acme.example',
    industry: 'Software',
    location: 'Berlin',
    notes: '',
    application_count: 0,
    created_at: '2026-11-01T10:00:00Z',
    updated_at: '2026-11-01T10:00:00Z',
    ...overrides,
  }
}

/** Handlers for a signed-in user with the given data. */
export function signedIn({
  applications = [] as Application[],
  companies = [] as Company[],
}: { applications?: Application[]; companies?: Company[] } = {}) {
  localStorage.setItem('careerops.token', fakeToken())
  server.use(
    http.get(`${API}/users/me`, () => HttpResponse.json(user)),
    http.get(`${API}/applications`, () =>
      HttpResponse.json(applications, { headers: { 'X-Total-Count': String(applications.length) } }),
    ),
    http.get(`${API}/companies`, () =>
      HttpResponse.json(companies, { headers: { 'X-Total-Count': String(companies.length) } }),
    ),
  )
}
