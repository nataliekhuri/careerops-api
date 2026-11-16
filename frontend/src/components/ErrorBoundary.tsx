import { RefreshCw } from 'lucide-react'
import { Component, type ErrorInfo, type ReactNode } from 'react'

import { Button } from './ui/Button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/**
 * Catches rendering errors (including a page's code failing to download, e.g. after a
 * new deploy or a dropped connection) and shows a recovery screen instead of a blank page.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    const chunkFailed = /dynamically imported module|Importing a module script failed|Loading chunk/i.test(
      this.state.error.message,
    )
    return (
      <div role="alert" className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <h1 className="text-xl font-semibold text-slate-900">
          {chunkFailed ? 'This page could not be loaded' : 'Something went wrong'}
        </h1>
        <p className="mt-2 max-w-md text-sm text-slate-500">
          {chunkFailed
            ? 'Your connection may have dropped, or CareerOps was just updated. Reloading usually fixes it.'
            : 'An unexpected error occurred. Reloading the page should get you going again.'}
        </p>
        <Button className="mt-6" onClick={() => window.location.reload()}>
          <RefreshCw className="size-4" aria-hidden /> Reload page
        </Button>
      </div>
    )
  }
}
