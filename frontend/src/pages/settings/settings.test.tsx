// Load the lazily routed page while the file is collected, so the first test measures
// behaviour rather than cold module compilation.
import '@/pages/settings/SettingsPage'
import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import { getToken } from '@/auth/token'
import { renderApp } from '@/test/render'
import { API, makeCareerProfile, server, signedIn, user as me } from '@/test/server'

describe('settings', () => {
  test('updates the profile name', async () => {
    signedIn()
    let body: unknown
    server.use(
      http.patch(`${API}/users/me`, async ({ request }) => {
        body = await request.json()
        return HttpResponse.json({ ...me, full_name: 'Ann Updated' })
      }),
    )
    const { user } = renderApp('/settings')

    const name = await screen.findByLabelText('Full name')
    await user.clear(name)
    await user.type(name, 'Ann Updated')
    await user.click(screen.getByRole('button', { name: 'Save profile' }))

    expect(await screen.findByText('Profile saved')).toBeInTheDocument()
    expect(body).toEqual({ full_name: 'Ann Updated' })
    expect(screen.getByLabelText('Email')).toHaveValue('ann@example.com')
  })

  test('shows a wrong current password next to the field', async () => {
    signedIn()
    server.use(
      http.post(`${API}/users/me/password`, () =>
        HttpResponse.json({ detail: 'Current password is incorrect' }, { status: 400 }),
      ),
    )
    const { user } = renderApp('/settings')

    await user.type(await screen.findByLabelText('Current password'), 'wrong-1')
    await user.type(screen.getByLabelText('New password'), 'new-password-9')
    await user.type(screen.getByLabelText('Confirm new password'), 'new-password-9')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(await screen.findByText('Current password is incorrect')).toBeInTheDocument()
  })

  test('checks that the new passwords match before sending', async () => {
    signedIn()
    const { user } = renderApp('/settings')

    await user.type(await screen.findByLabelText('Current password'), 'old-pass-1')
    await user.type(screen.getByLabelText('New password'), 'new-password-9')
    await user.type(screen.getByLabelText('Confirm new password'), 'different-9')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument()
  })

  test('changes the password', async () => {
    signedIn()
    let body: unknown
    server.use(
      http.post(`${API}/users/me/password`, async ({ request }) => {
        body = await request.json()
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { user } = renderApp('/settings')

    await user.type(await screen.findByLabelText('Current password'), 'old-pass-1')
    await user.type(screen.getByLabelText('New password'), 'new-password-9')
    await user.type(screen.getByLabelText('Confirm new password'), 'new-password-9')
    await user.click(screen.getByRole('button', { name: 'Change password' }))

    expect(await screen.findByText('Password changed')).toBeInTheDocument()
    expect(body).toEqual({ current_password: 'old-pass-1', new_password: 'new-password-9' })
  })

  test('deleting the account needs the password and a confirmation, then signs out', async () => {
    signedIn()
    let body: unknown
    server.use(
      http.delete(`${API}/users/me`, async ({ request }) => {
        body = await request.json()
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { user } = renderApp('/settings')

    const button = await screen.findByRole('button', { name: 'Delete my account' })
    expect(button).toBeDisabled()
    await user.type(screen.getByLabelText('Password'), 'my-pass-1')
    expect(button).toBeDisabled()
    await user.click(screen.getByRole('checkbox', { name: /permanently deleted/ }))
    await user.click(button)

    expect(await screen.findByRole('heading', { name: /Stay on top of every job application/ })).toBeInTheDocument()
    expect(body).toEqual({ password: 'my-pass-1' })
    await waitFor(() => expect(getToken()).toBeNull())
  })

  test('a wrong password does not delete anything', async () => {
    signedIn()
    server.use(
      http.delete(`${API}/users/me`, () => HttpResponse.json({ detail: 'Password is incorrect' }, { status: 400 })),
    )
    const { user } = renderApp('/settings')

    await user.type(await screen.findByLabelText('Password'), 'wrong-1')
    await user.click(screen.getByRole('checkbox', { name: /permanently deleted/ }))
    await user.click(screen.getByRole('button', { name: 'Delete my account' }))

    expect(await screen.findByText('Password is incorrect')).toBeInTheDocument()
    expect(getToken()).not.toBeNull()
  })

  test('loads and saves the career profile', async () => {
    signedIn({
      careerProfile: makeCareerProfile({
        headline: 'Backend developer',
        skills: ['Python', 'Basket weaving'],
        recognized_skills: ['Python'],
        unrecognized_skills: ['Basket weaving'],
      }),
    })
    let body: Record<string, unknown> = {}
    server.use(
      http.put(`${API}/users/me/career-profile`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(
          makeCareerProfile({ ...body, recognized_skills: ['Docker', 'Python'], updated_at: '2026-11-13T10:00:00Z' }),
        )
      }),
    )
    const { user } = renderApp('/settings')

    const form = await screen.findByRole('form', { name: 'Career profile' })
    const skills = within(form).getByLabelText('Skills')
    await waitFor(() => expect(skills).toHaveValue('Python, Basket weaving'))
    expect(within(form).getByText(/Basket weaving/, { selector: 'p' })).toBeInTheDocument()
    await user.clear(skills)
    await user.type(skills, 'Python, Docker,, ')
    await user.type(within(form).getByLabelText('Years of experience'), '4')
    await user.type(within(form).getByLabelText('CV (plain text)'), 'Built APIs')
    await user.click(within(form).getByRole('button', { name: 'Save career profile' }))

    expect(await screen.findByText('Career profile saved')).toBeInTheDocument()
    expect(body).toEqual({
      headline: 'Backend developer',
      target_role: '',
      years_experience: 4,
      skills: ['Python', 'Docker'],
      cv_text: 'Built APIs',
    })
    expect(within(screen.getByRole('list', { name: 'Recognised skills' })).getByText('Docker')).toBeInTheDocument()
  })

  test('validates the career profile before sending', async () => {
    signedIn()
    const { user } = renderApp('/settings')

    const form = await screen.findByRole('form', { name: 'Career profile' })
    await user.type(within(form).getByLabelText('Years of experience'), 'ten')
    await user.click(within(form).getByRole('button', { name: 'Save career profile' }))

    expect(await within(form).findByText('Use a whole number from 0 to 60')).toBeInTheDocument()
  })

  test('shows an error when the career profile cannot load', async () => {
    signedIn()
    server.use(http.get(`${API}/users/me/career-profile`, () => HttpResponse.json({}, { status: 503 })))
    renderApp('/settings')

    expect(await screen.findByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})
