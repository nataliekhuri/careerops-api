// Load the lazily routed page while the file is collected, so the first test measures
// behaviour rather than cold module compilation.
import '@/pages/interviews/InterviewsPage'
import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import { localDateTimeToIso, monthGrid, startOfMonth, toDateInput } from '@/lib/dates'
import { renderApp } from '@/test/render'
import { API, makeApplication, makeInterview, server, signedIn } from '@/test/server'

function todayAt(hours: number, minutes = 0): string {
  const date = new Date()
  date.setHours(hours, minutes, 0, 0)
  return date.toISOString()
}

describe('interview calendar', () => {
  test("requests the visible weeks and lists today's interviews", async () => {
    const requests: URL[] = []
    signedIn()
    server.use(
      http.get(`${API}/interviews`, ({ request }) => {
        requests.push(new URL(request.url))
        return HttpResponse.json([makeInterview({ id: 5, scheduled_at: todayAt(15) })], {
          headers: { 'X-Total-Count': '1' },
        })
      }),
    )
    renderApp('/interviews')

    const list = await screen.findByRole('list', { name: 'Interviews on the selected day' })
    expect(within(list).getByRole('link', { name: 'Acme Corp · Backend Developer' })).toBeInTheDocument()
    expect(within(list).getByRole('link', { name: /Join meeting/ })).toHaveAttribute('href', 'https://meet.example/abc')

    const grid = monthGrid(startOfMonth(new Date()))
    const first = requests[0]!
    expect(new Date(first.searchParams.get('start')!).getTime()).toBe(grid[0]!.getTime())
    expect(first.searchParams.get('end')).not.toBeNull()
  })

  test('next month requests a later range', async () => {
    const starts: string[] = []
    signedIn()
    server.use(
      http.get(`${API}/interviews`, ({ request }) => {
        starts.push(new URL(request.url).searchParams.get('start')!)
        return HttpResponse.json([], { headers: { 'X-Total-Count': '0' } })
      }),
    )
    const { user } = renderApp('/interviews')

    await user.click(await screen.findByRole('button', { name: 'Next month' }))

    await waitFor(() => expect(starts.length).toBeGreaterThanOrEqual(2))
    expect(new Date(starts.at(-1)!).getTime()).toBeGreaterThan(new Date(starts[0]!).getTime())
  })

  test('schedules an interview with a timezone-aware time', async () => {
    signedIn({ applications: [makeApplication({ id: 4, company: 'Globex', position: 'API Engineer' })] })
    let body: Record<string, unknown> = {}
    server.use(
      http.post(`${API}/interviews`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(
          makeInterview({
            id: 9,
            scheduled_at: body.scheduled_at as string,
            application: { id: 4, company: 'Globex', position: 'API Engineer', status: 'Applied' },
          }),
          { status: 201 },
        )
      }),
    )
    const { user } = renderApp('/interviews')

    await user.click(await screen.findByRole('button', { name: 'Schedule interview' }))
    const dialog = await screen.findByRole('dialog')
    await within(dialog).findByRole('option', { name: 'Globex — API Engineer' })
    await user.selectOptions(within(dialog).getByLabelText('Application'), 'Globex — API Engineer')
    await user.clear(within(dialog).getByLabelText('Time'))
    await user.type(within(dialog).getByLabelText('Time'), '14:30')
    await user.selectOptions(within(dialog).getByLabelText('Type'), 'Technical')
    await user.click(within(dialog).getByRole('button', { name: 'Schedule interview' }))

    expect(await screen.findByText('Interview with Globex scheduled')).toBeInTheDocument()
    expect(body).toMatchObject({
      application_id: 4,
      interview_type: 'technical',
      duration_minutes: 60,
      scheduled_at: localDateTimeToIso(toDateInput(new Date()), '14:30'),
    })
    expect(String(body.scheduled_at)).toMatch(/Z$/) // always sent with a time zone
  })

  test('validates the form before sending', async () => {
    signedIn()
    const { user } = renderApp('/interviews')

    await user.click(await screen.findByRole('button', { name: 'Schedule interview' }))
    const dialog = await screen.findByRole('dialog')
    await user.clear(within(dialog).getByLabelText('Duration (minutes)'))
    await user.type(within(dialog).getByLabelText('Duration (minutes)'), '0')
    await user.click(within(dialog).getByRole('button', { name: 'Schedule interview' }))

    expect(await within(dialog).findByText('Choose the application')).toBeInTheDocument()
    expect(within(dialog).getByText('Use 1 to 600 minutes')).toBeInTheDocument()
  })

  test('records an outcome and deletes an interview', async () => {
    signedIn({ interviews: [makeInterview({ id: 5, scheduled_at: todayAt(11) })] })
    let patched: Record<string, unknown> = {}
    let deleted = false
    server.use(
      http.patch(`${API}/interviews/5`, async ({ request }) => {
        patched = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(makeInterview({ id: 5, scheduled_at: todayAt(11), outcome: 'passed' }))
      }),
      http.delete(`${API}/interviews/5`, () => {
        deleted = true
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { user } = renderApp('/interviews')

    const list = await screen.findByRole('list', { name: 'Interviews on the selected day' })
    await user.click(within(list).getByRole('button', { name: 'Edit' }))
    const dialog = await screen.findByRole('dialog')
    await user.selectOptions(within(dialog).getByLabelText('Outcome'), 'Passed')
    await user.click(within(dialog).getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(patched.outcome).toBe('passed'))

    await user.click(within(list).getByRole('button', { name: 'Delete' }))
    await user.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Delete interview' }))
    await waitFor(() => expect(deleted).toBe(true))
  })

  test('shows an API error for a foreign or missing application', async () => {
    signedIn({ applications: [makeApplication({ id: 4, company: 'Globex', position: 'API Engineer' })] })
    server.use(
      http.post(`${API}/interviews`, () =>
        HttpResponse.json(
          { detail: [{ type: 'not_found', loc: ['body', 'application_id'], msg: 'Application not found' }] },
          { status: 422 },
        ),
      ),
    )
    const { user } = renderApp('/interviews')

    await user.click(await screen.findByRole('button', { name: 'Schedule interview' }))
    const dialog = await screen.findByRole('dialog')
    await within(dialog).findByRole('option', { name: 'Globex — API Engineer' })
    await user.selectOptions(within(dialog).getByLabelText('Application'), 'Globex — API Engineer')
    await user.click(within(dialog).getByRole('button', { name: 'Schedule interview' }))

    expect(await within(dialog).findByText('Application not found')).toBeInTheDocument()
  })
})
