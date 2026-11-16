import { screen } from '@testing-library/react'
import { describe, expect, test } from 'vitest'

import { renderApp } from '@/test/render'

describe('public pages', () => {
  test('landing page lists the AI assistant among the features and links to the privacy notice', async () => {
    renderApp('/')

    expect(screen.getByRole('heading', { name: 'Stay on top of every job application' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'AI career assistant' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Privacy notice' })).toHaveAttribute('href', '/privacy')
  })

  test('privacy page explains the built-in analyzer and account deletion', async () => {
    renderApp('/privacy')

    expect(await screen.findByRole('heading', { name: 'How CareerOps handles your data' })).toBeInTheDocument()
    expect(screen.getByText(/free, rule-based analyzer that runs on/)).toBeInTheDocument()
    expect(screen.getByText(/nothing you enter.*is sent to/)).toBeInTheDocument()
    expect(screen.getByText(/Settings → Delete account/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to home' })).toHaveAttribute('href', '/')
  })

  test('the register page links to the privacy notice', async () => {
    renderApp('/register')

    expect(await screen.findByRole('heading', { name: 'Create your account' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'privacy notice' })).toHaveAttribute('href', '/privacy')
  })
})
