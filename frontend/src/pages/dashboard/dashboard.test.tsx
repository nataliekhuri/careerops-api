// Load the lazily routed page while the file is collected, so the first test measures
// behaviour rather than cold module compilation.
import '@/pages/dashboard/DashboardPage'
import { screen, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import { renderApp } from '@/test/render'
import { API, emptyStats, makeInterview, server, signedIn } from '@/test/server'

const STATS = emptyStats({
  total_applications: 10,
  active_applications: 8,
  by_status: { Applied: 4, Screening: 1, Interview: 2, Offer: 1, Rejected: 1, Withdrawn: 1 },
  rates: { response_rate: 55.6, interview_rate: 33.3, offer_rate: 11.1 },
  top_companies: [
    { company: 'Acme Corp', count: 3 },
    { company: 'Globex', count: 2 },
  ],
  total_interviews: 4,
  upcoming_interviews_count: 2,
  upcoming_interviews: [
    makeInterview({ id: 7, application: { id: 3, company: 'Initech', position: 'SRE', status: 'Interview' } }),
  ],
})

describe('dashboard', () => {
  test('shows key figures, rates and lists from the API', async () => {
    signedIn({ stats: STATS })
    renderApp('/dashboard')

    const figures = (await screen.findByText('8 still active')).closest('section')!
    expect(figures).toHaveAttribute('aria-label', 'Key figures')
    expect(within(figures).getByText('10')).toBeInTheDocument()
    expect(within(figures).getByText('8 still active')).toBeInTheDocument()
    expect(within(figures).getByText('55.6%')).toBeInTheDocument()
    expect(within(figures).getByText('Offer rate 11.1%')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Acme Corp' })).toHaveAttribute('href', '/applications?q=Acme%20Corp')
    expect(screen.getByRole('link', { name: /Initech · SRE/ })).toHaveAttribute('href', '/applications/3')
  })

  test('pipeline rows link to the filtered applications list', async () => {
    signedIn({ stats: STATS })
    renderApp('/dashboard')

    expect(await screen.findByRole('link', { name: 'Offer' })).toHaveAttribute('href', '/applications?status=Offer')
  })

  test('the weekly chart has a text alternative', async () => {
    signedIn({
      stats: { ...STATS, applications_per_week: STATS.applications_per_week.map((w, i) => ({ ...w, count: i })) },
    })
    renderApp('/dashboard')

    expect(await screen.findByText(/Applications per week for the last 12 weeks: 66 in total/)).toBeInTheDocument()
  })

  test('new users see a helpful empty state', async () => {
    signedIn()
    renderApp('/dashboard')

    expect(await screen.findByText('Your dashboard fills up as you apply')).toBeInTheDocument()
  })

  test('shows an error with retry when statistics cannot load', async () => {
    signedIn()
    server.use(http.get(`${API}/dashboard/stats`, () => HttpResponse.json({}, { status: 503 })))
    renderApp('/dashboard')

    expect(await screen.findByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})
