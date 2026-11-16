import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

import type { Application, CareerProfile, Company, DashboardStats, Interview, SkillInsights, User } from '@/api/types'

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
    job_description: '',
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

export function emptyStats(overrides: Partial<DashboardStats> = {}): DashboardStats {
  return {
    total_applications: 0,
    active_applications: 0,
    by_status: { Applied: 0, Screening: 0, Interview: 0, Offer: 0, Rejected: 0, Withdrawn: 0 },
    rates: { response_rate: 0, interview_rate: 0, offer_rate: 0 },
    applications_per_week: Array.from({ length: 12 }, (_, i) => ({
      week_start: new Date(Date.UTC(2026, 7, 24 + i * 7)).toISOString().slice(0, 10),
      count: 0,
    })),
    top_companies: [],
    total_companies: 0,
    total_interviews: 0,
    upcoming_interviews_count: 0,
    upcoming_interviews: [],
    ...overrides,
  }
}

export function makeInterview(overrides: Partial<Interview> = {}): Interview {
  return {
    id: 1,
    application_id: 1,
    application: { id: 1, company: 'Acme Corp', position: 'Backend Developer', status: 'Interview' },
    scheduled_at: '2026-11-20T09:00:00Z',
    duration_minutes: 60,
    interview_type: 'video',
    location: 'https://meet.example/abc',
    interviewer: 'Jane Doe',
    notes: '',
    outcome: 'pending',
    created_at: '2026-11-01T10:00:00Z',
    updated_at: '2026-11-01T10:00:00Z',
    ...overrides,
  }
}

export function makeCareerProfile(overrides: Partial<CareerProfile> = {}): CareerProfile {
  return {
    headline: '',
    target_role: '',
    years_experience: null,
    skills: [],
    cv_text: '',
    recognized_skills: [],
    unrecognized_skills: [],
    updated_at: null,
    ...overrides,
  }
}

export function emptyInsights(overrides: Partial<SkillInsights> = {}): SkillInsights {
  return {
    analyzed_applications: 0,
    total_applications: 0,
    coverage_percent: null,
    skills: [],
    top_missing: [],
    ...overrides,
  }
}

/** Handlers for a signed-in user with the given data. */
export function signedIn({
  applications = [] as Application[],
  companies = [] as Company[],
  interviews = [] as Interview[],
  stats = emptyStats(),
  careerProfile = makeCareerProfile(),
  insights = emptyInsights(),
}: {
  applications?: Application[]
  companies?: Company[]
  interviews?: Interview[]
  stats?: DashboardStats
  careerProfile?: CareerProfile
  insights?: SkillInsights
} = {}) {
  localStorage.setItem('careerops.token', fakeToken())
  server.use(
    http.get(`${API}/users/me`, () => HttpResponse.json(user)),
    http.get(`${API}/applications`, () =>
      HttpResponse.json(applications, { headers: { 'X-Total-Count': String(applications.length) } }),
    ),
    http.get(`${API}/companies`, () =>
      HttpResponse.json(companies, { headers: { 'X-Total-Count': String(companies.length) } }),
    ),
    http.get(`${API}/interviews`, () =>
      HttpResponse.json(interviews, { headers: { 'X-Total-Count': String(interviews.length) } }),
    ),
    http.get(`${API}/dashboard/stats`, () => HttpResponse.json(stats)),
    http.get(`${API}/users/me/career-profile`, () => HttpResponse.json(careerProfile)),
    http.get(`${API}/ai/skill-insights`, () => HttpResponse.json(insights)),
    http.get(`${API}/ai/provider`, () =>
      HttpResponse.json({
        name: 'builtin',
        external: false,
        cost: 'free',
        description: 'Built-in rule-based analyzer. Runs on this server; your data is not sent anywhere.',
      }),
    ),
  )
}
