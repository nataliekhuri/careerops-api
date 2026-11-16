// Load the lazily routed page while the file is collected, so the first test measures
// behaviour rather than cold module compilation.
import '@/pages/board/BoardPage'
import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import { renderApp } from '@/test/render'
import { API, makeApplication, server, signedIn } from '@/test/server'

const APPS = [
  makeApplication({ id: 1, company: 'Acme Corp', status: 'Applied' }),
  makeApplication({ id: 2, company: 'Globex', status: 'Applied' }),
  makeApplication({ id: 3, company: 'Initech', status: 'Interview' }),
]

function column(name: string) {
  return screen.getByRole('heading', { name: new RegExp(`^${name}`) }).closest('section')!
}

describe('board', () => {
  test('groups applications into status columns with counts', async () => {
    signedIn({ applications: APPS })
    renderApp('/board')

    await screen.findByRole('heading', { name: /^Applied/ })
    expect(within(column('Applied')).getAllByRole('listitem')).toHaveLength(2)
    expect(within(column('Interview')).getByText('Initech')).toBeInTheDocument()
    expect(within(column('Offer')).getByText('Drop here')).toBeInTheDocument()
  })

  test('loads every page of applications (the API returns at most 100)', async () => {
    signedIn()
    const many = Array.from({ length: 150 }, (_, i) => makeApplication({ id: i + 1, company: `Company ${i + 1}` }))
    const offsets: string[] = []
    server.use(
      http.get(`${API}/applications`, ({ request }) => {
        const url = new URL(request.url)
        const offset = Number(url.searchParams.get('offset'))
        offsets.push(String(offset))
        return HttpResponse.json(many.slice(offset, offset + 100), { headers: { 'X-Total-Count': '150' } })
      }),
    )
    renderApp('/board')

    await waitFor(() => expect(within(column('Applied')).getAllByRole('listitem')).toHaveLength(150))
    expect(offsets).toEqual(['0', '100'])
  })

  test('moving a card updates the API and shows it in the new column', async () => {
    // A tiny stateful fake API, so the refetch after the move returns the new status.
    const apps = APPS.map((a) => ({ ...a }))
    signedIn()
    let patched: unknown
    server.use(
      http.get(`${API}/applications`, () =>
        HttpResponse.json(apps, { headers: { 'X-Total-Count': String(apps.length) } }),
      ),
      http.patch(`${API}/applications/1`, async ({ request }) => {
        patched = await request.json()
        apps[0] = { ...apps[0]!, status: 'Offer' }
        return HttpResponse.json(apps[0])
      }),
    )
    const { user } = renderApp('/board')

    await user.selectOptions(await screen.findByLabelText('Move Backend Developer at Acme Corp to'), 'Offer')

    await waitFor(() => expect(within(column('Offer')).getByText('Acme Corp')).toBeInTheDocument())
    await waitFor(() => expect(patched).toEqual({ status: 'Offer' }))
    expect(await screen.findByText('Acme Corp moved to Offer')).toBeInTheDocument()
  })

  test('a failed move puts the card back and explains why', async () => {
    signedIn({ applications: APPS })
    server.use(
      http.patch(`${API}/applications/1`, () =>
        HttpResponse.json({ detail: 'Application not found' }, { status: 404 }),
      ),
    )
    const { user } = renderApp('/board')

    await user.selectOptions(await screen.findByLabelText('Move Backend Developer at Acme Corp to'), 'Rejected')

    expect(await screen.findByText('Could not move Acme Corp: Application not found')).toBeInTheDocument()
    await waitFor(() => expect(within(column('Applied')).getByText('Acme Corp')).toBeInTheDocument())
    expect(within(column('Rejected')).queryByText('Acme Corp')).not.toBeInTheDocument()
  })

  test('cards have an accessible drag handle', async () => {
    signedIn({ applications: APPS })
    renderApp('/board')

    expect(await screen.findByRole('button', { name: 'Drag Backend Developer at Globex' })).toBeInTheDocument()
  })

  test('shows an empty state', async () => {
    signedIn()
    renderApp('/board')

    expect(await screen.findByText('Your board is empty')).toBeInTheDocument()
  })
})
