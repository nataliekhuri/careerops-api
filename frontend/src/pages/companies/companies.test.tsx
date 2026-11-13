import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import { renderApp } from '@/test/render'
import { API, makeApplication, makeCompany, server, signedIn } from '@/test/server'

describe('companies', () => {
  test('lists companies with application counts', async () => {
    signedIn({ companies: [makeCompany({ id: 3, name: 'Globex', application_count: 2 })] })
    renderApp('/companies')

    const link = await screen.findByRole('link', { name: /Globex/ })
    expect(link).toHaveAttribute('href', '/companies/3')
    expect(within(link).getByText('2 applications')).toBeInTheDocument()
  })

  test('creates a company and opens it', async () => {
    signedIn()
    let body: unknown
    server.use(
      http.post(`${API}/companies`, async ({ request }) => {
        body = await request.json()
        return HttpResponse.json(makeCompany({ id: 9, name: 'Umbrella' }), { status: 201 })
      }),
      http.get(`${API}/companies/9`, () => HttpResponse.json(makeCompany({ id: 9, name: 'Umbrella' }))),
    )
    const { user } = renderApp('/companies')

    await user.click(await screen.findByRole('button', { name: 'New company' }))
    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText('Name'), 'Umbrella')
    await user.type(within(dialog).getByLabelText('Website'), 'https://umbrella.example')
    await user.click(within(dialog).getByRole('button', { name: 'Save company' }))

    expect(await screen.findByRole('heading', { name: 'Umbrella' })).toBeInTheDocument()
    expect(body).toMatchObject({ name: 'Umbrella', website: 'https://umbrella.example' })
  })

  test('rejects a website without http(s) before sending', async () => {
    signedIn()
    const { user } = renderApp('/companies')

    await user.click(await screen.findByRole('button', { name: 'New company' }))
    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText('Name'), 'Umbrella')
    await user.type(within(dialog).getByLabelText('Website'), 'umbrella.example')
    await user.click(within(dialog).getByRole('button', { name: 'Save company' }))

    expect(await within(dialog).findByText('Start with http:// or https://')).toBeInTheDocument()
  })

  test('shows the duplicate-name error on the name field', async () => {
    signedIn()
    server.use(
      http.post(`${API}/companies`, () =>
        HttpResponse.json({ detail: 'You already have a company with this name' }, { status: 409 }),
      ),
    )
    const { user } = renderApp('/companies')

    await user.click(await screen.findByRole('button', { name: 'New company' }))
    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText('Name'), 'Acme')
    await user.click(within(dialog).getByRole('button', { name: 'Save company' }))

    expect(await within(dialog).findByText('You already have a company with this name')).toBeInTheDocument()
  })

  test('company page lists its linked applications', async () => {
    signedIn()
    const requested: URL[] = []
    server.use(
      http.get(`${API}/companies/3`, () =>
        HttpResponse.json(makeCompany({ id: 3, name: 'Globex', application_count: 1 })),
      ),
      http.get(`${API}/applications`, ({ request }) => {
        requested.push(new URL(request.url))
        return HttpResponse.json([makeApplication({ id: 11, position: 'SRE', company_id: 3 })], {
          headers: { 'X-Total-Count': '1' },
        })
      }),
    )
    renderApp('/companies/3')

    expect(await screen.findByRole('link', { name: /SRE/ })).toHaveAttribute('href', '/applications/11')
    await waitFor(() => expect(requested.at(-1)?.searchParams.get('company_id')).toBe('3'))
  })

  test('deleting a company explains that applications are kept', async () => {
    signedIn()
    let deleted = false
    server.use(
      http.get(`${API}/companies/3`, () => HttpResponse.json(makeCompany({ id: 3, name: 'Globex' }))),
      http.delete(`${API}/companies/3`, () => {
        deleted = true
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { user } = renderApp('/companies/3')

    await user.click(await screen.findByRole('button', { name: 'Delete' }))
    const dialog = await screen.findByRole('alertdialog')
    expect(within(dialog).getByText(/Linked applications are kept/)).toBeInTheDocument()
    await user.click(within(dialog).getByRole('button', { name: 'Delete company' }))

    await waitFor(() => expect(deleted).toBe(true))
    expect(await screen.findByRole('heading', { name: 'Companies' })).toBeInTheDocument()
  })
})
