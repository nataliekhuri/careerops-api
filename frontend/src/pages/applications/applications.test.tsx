import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import { renderApp } from '@/test/render'
import { API, makeApplication, makeCompany, server, signedIn } from '@/test/server'

describe('applications list', () => {
  test('shows applications with their status and total', async () => {
    signedIn({
      applications: [
        makeApplication({ id: 1, company: 'Acme Corp', status: 'Interview' }),
        makeApplication({ id: 2, company: 'Globex', status: 'Offer' }),
      ],
    })
    renderApp('/applications')

    const table = await screen.findByRole('table')
    expect(within(table).getByRole('link', { name: 'Acme Corp' })).toHaveAttribute('href', '/applications/1')
    expect(within(table).getByText('Offer')).toBeInTheDocument()
    expect(screen.getByText('2 applications')).toBeInTheDocument()
  })

  test('sends search, status filter and sort to the API', async () => {
    signedIn()
    const requests: URL[] = []
    server.use(
      http.get(`${API}/applications`, ({ request }) => {
        requests.push(new URL(request.url))
        return HttpResponse.json([], { headers: { 'X-Total-Count': '0' } })
      }),
    )
    const { user } = renderApp('/applications')

    await user.selectOptions(await screen.findByLabelText('Filter by status'), 'Interview')
    await user.selectOptions(screen.getByLabelText('Sort'), 'company')
    await user.type(screen.getByLabelText('Search by company'), 'acme')

    await waitFor(() => {
      const last = requests.at(-1)!
      expect(last.searchParams.get('status')).toBe('Interview')
      expect(last.searchParams.get('sort')).toBe('company')
      expect(last.searchParams.get('company')).toBe('acme')
      expect(last.searchParams.get('offset')).toBe('0')
    })
  })

  test('paginates using the total count header', async () => {
    signedIn()
    const offsets: (string | null)[] = []
    server.use(
      http.get(`${API}/applications`, ({ request }) => {
        offsets.push(new URL(request.url).searchParams.get('offset'))
        return HttpResponse.json([makeApplication()], { headers: { 'X-Total-Count': '45' } })
      }),
    )
    const { user } = renderApp('/applications')

    const pagination = await screen.findByRole('navigation', { name: 'Pagination' })
    expect(pagination).toHaveTextContent('Showing 1–20 of 45')
    await user.click(screen.getByRole('button', { name: /Next/ }))

    await waitFor(() => expect(offsets.at(-1)).toBe('20'))
    await waitFor(() =>
      expect(screen.getByRole('navigation', { name: 'Pagination' })).toHaveTextContent('Showing 21–40 of 45'),
    )
  })

  test('shows a helpful empty state', async () => {
    signedIn()
    renderApp('/applications')
    expect(await screen.findByText('No applications yet')).toBeInTheDocument()
  })

  test('shows a server error with a retry option', async () => {
    signedIn()
    server.use(http.get(`${API}/applications`, () => HttpResponse.json({}, { status: 500 })))
    renderApp('/applications')
    expect(await screen.findByText(/Something went wrong on our side/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})

describe('creating and editing', () => {
  test('creates an application linked to a company', async () => {
    signedIn({ companies: [makeCompany({ id: 7, name: 'Initech' })] })
    let body: Record<string, unknown> = {}
    server.use(
      http.post(`${API}/applications`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({
          message: 'Application created successfully',
          application: makeApplication({ id: 42, ...body }),
        })
      }),
      http.get(`${API}/applications/42`, () => HttpResponse.json(makeApplication({ id: 42, ...body }))),
    )
    const { user } = renderApp('/applications/new')

    await screen.findByRole('option', { name: 'Initech' }) // wait for the company list
    await user.selectOptions(screen.getByLabelText('Linked company (optional)'), 'Initech')
    // Picking a company fills in the empty company name.
    expect(screen.getByLabelText('Company')).toHaveValue('Initech')
    await user.type(screen.getByLabelText('Position'), 'Platform Engineer')
    await user.type(screen.getByLabelText('Location'), 'Remote')
    await user.click(screen.getByRole('button', { name: 'Save application' }))

    expect(await screen.findByRole('heading', { name: 'Platform Engineer' })).toBeInTheDocument()
    expect(body).toMatchObject({
      company: 'Initech',
      position: 'Platform Engineer',
      location: 'Remote',
      status: 'Applied',
      company_id: 7,
    })
  })

  test('shows required-field errors without calling the API', async () => {
    signedIn()
    const { user } = renderApp('/applications/new')

    await user.click(await screen.findByRole('button', { name: 'Save application' }))

    expect(await screen.findByText('Enter the company name')).toBeInTheDocument()
    expect(screen.getByText('Enter the job title')).toBeInTheDocument()
  })

  test('changes status from the details page', async () => {
    signedIn()
    let patched: unknown
    server.use(
      http.get(`${API}/applications/5`, () => HttpResponse.json(makeApplication({ id: 5 }))),
      http.patch(`${API}/applications/5`, async ({ request }) => {
        patched = await request.json()
        return HttpResponse.json(makeApplication({ id: 5, status: 'Interview' }))
      }),
    )
    const { user } = renderApp('/applications/5')

    await user.selectOptions(await screen.findByLabelText('Status'), 'Interview')

    await waitFor(() => expect(patched).toEqual({ status: 'Interview' }))
    expect(await screen.findByText('Status changed to Interview')).toBeInTheDocument()
  })

  test('deletes after confirmation', async () => {
    signedIn()
    let deleted = false
    server.use(
      http.get(`${API}/applications/5`, () => HttpResponse.json(makeApplication({ id: 5 }))),
      http.delete(`${API}/applications/5`, () => {
        deleted = true
        return HttpResponse.json({ message: 'deleted', application: makeApplication({ id: 5 }) })
      }),
    )
    const { user } = renderApp('/applications/5')

    await user.click(await screen.findByRole('button', { name: 'Delete' }))
    const dialog = await screen.findByRole('alertdialog')
    await user.click(within(dialog).getByRole('button', { name: 'Delete application' }))

    await waitFor(() => expect(deleted).toBe(true))
    expect(await screen.findByRole('heading', { name: 'Applications' })).toBeInTheDocument()
  })

  test('an unknown or foreign application shows "not found"', async () => {
    signedIn()
    server.use(
      http.get(`${API}/applications/999`, () =>
        HttpResponse.json({ detail: 'Application not found' }, { status: 404 }),
      ),
    )
    renderApp('/applications/999')
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
  })
})
