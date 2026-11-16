import { render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import { ErrorBoundary } from './ErrorBoundary'

function Broken({ message }: { message: string }): never {
  throw new Error(message)
}

describe('ErrorBoundary', () => {
  test('shows a reload screen when a page fails to download', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <Broken message="Failed to fetch dynamically imported module: /src/pages/AuthPages.tsx" />
      </ErrorBoundary>,
    )
    expect(screen.getByRole('heading', { name: 'This page could not be loaded' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reload page' })).toBeInTheDocument()
  })

  test('shows a generic message for other errors', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <Broken message="boom" />
      </ErrorBoundary>,
    )
    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeInTheDocument()
  })

  test('renders children when nothing fails', () => {
    render(
      <ErrorBoundary>
        <p>All good</p>
      </ErrorBoundary>,
    )
    expect(screen.getByText('All good')).toBeInTheDocument()
  })
})
