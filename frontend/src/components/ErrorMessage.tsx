import { AlertCircle } from 'lucide-react'

import { errorText } from '@/lib/errors'

export function ErrorMessage({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-lg bg-red-50 p-4 text-sm text-red-800 ring-1 ring-red-200"
    >
      <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="flex-1">
        <p>{errorText(error)}</p>
        {onRetry && (
          <button type="button" onClick={onRetry} className="mt-2 font-medium underline underline-offset-2">
            Try again
          </button>
        )}
      </div>
    </div>
  )
}
