// Load the lazily routed pages these tests visit while the file is collected, so the
// first test measures behaviour rather than cold module compilation.
import '@/layouts/AppLayout'
import '@/pages/AuthPages'
import '@/pages/dashboard/DashboardPage'
import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import { API, emptyStats, fakeToken, server, signedIn, user as me } from '@/test/server'
import { renderApp } from '@/test/render'

import { getToken } from './token'

describe('token storage', () => {
  test('returns a valid token and drops an expired one', () => {
    localStorage.setItem('careerops.token', fakeToken(60))
    expect(getToken()).not.toBeNull()

    localStorage.setItem('careerops.token', fakeToken(-1))
    expect(getToken()).toBeNull()
    expect(localStorage.getItem('careerops.token')).toBeNull()
  })

  test('ignores a malformed token', () => {
    localStorage.setItem('careerops.token', 'not-a-jwt')
    expect(getToken()).toBeNull()
  })
})

describe('protected routes', () => {
  test('redirect to login when signed out', async () => {
    renderApp('/applications')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  test('a rejected token signs the user out', async () => {
    localStorage.setItem('careerops.token', fakeToken())
    server.use(
      http.get(`${API}/users/me`, () =>
        HttpResponse.json({ detail: 'Could not validate credentials' }, { status: 401 }),
      ),
    )
    renderApp('/applications')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(localStorage.getItem('careerops.token')).toBeNull()
  })
})

describe('login', () => {
  test('signs in with the real form and opens the dashboard', async () => {
    let sentBody = ''
    server.use(
      http.post(`${API}/auth/login`, async ({ request }) => {
        sentBody = await request.text()
        return HttpResponse.json({ access_token: fakeToken(), token_type: 'bearer', expires_in: 3600 })
      }),
      http.get(`${API}/users/me`, () => HttpResponse.json(me)),
      http.get(`${API}/dashboard/stats`, () => HttpResponse.json(emptyStats())),
    )
    const { user } = renderApp('/login')

    await user.type(await screen.findByLabelText('Email'), 'ann@example.com')
    await user.type(screen.getByLabelText('Password'), 'secret-pass-1')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { name: 'Welcome back, Ann' })).toBeInTheDocument()
    expect(new URLSearchParams(sentBody).get('username')).toBe('ann@example.com')
    expect(getToken()).not.toBeNull()
  })

  test('shows the API error for wrong credentials', async () => {
    server.use(
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({ detail: 'Incorrect email or password' }, { status: 401 }),
      ),
    )
    const { user } = renderApp('/login')

    await user.type(await screen.findByLabelText('Email'), 'ann@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong-pass-1')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Incorrect email or password')).toBeInTheDocument()
    expect(getToken()).toBeNull()
  })

  test('validates before sending', async () => {
    let called = false
    server.use(http.post(`${API}/auth/login`, () => ((called = true), HttpResponse.json({}))))
    const { user } = renderApp('/login')

    await user.click(await screen.findByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Enter your email')).toBeInTheDocument()
    expect(called).toBe(false)
  })
})

describe('registration', () => {
  test('checks the password rules locally', async () => {
    const { user } = renderApp('/register')

    await user.type(await screen.findByLabelText('Email'), 'new@example.com')
    await user.type(screen.getByLabelText('Password'), 'onlyletters')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('Mix letters with numbers or symbols')).toBeInTheDocument()
  })

  test('shows a duplicate-email error from the API on the email field', async () => {
    server.use(
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json(
          { detail: [{ loc: ['body', 'email'], msg: 'An account with this email already exists', type: 'x' }] },
          { status: 422 },
        ),
      ),
    )
    const { user } = renderApp('/register')

    await user.type(await screen.findByLabelText('Email'), 'ann@example.com')
    await user.type(screen.getByLabelText('Password'), 'secret-pass-1')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('An account with this email already exists')).toBeInTheDocument()
  })

  test('signed-in users are sent from /login to their dashboard', async () => {
    signedIn()
    renderApp('/login')
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Welcome back, Ann' })).toBeInTheDocument())
  })
})
