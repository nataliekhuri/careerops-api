import '@testing-library/jest-dom/vitest'

import { cleanup, configure } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'

import { server } from './server'

// The first render of a lazily loaded page is slow on a cold start (fresh checkout / CI),
// so wait up to 10 s for async UI. Passing tests are not slowed down by this.
configure({ asyncUtilTimeout: 10_000 })

// Any request without a matching mock fails the test, so nothing reaches a real network.
beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  localStorage.clear()
})
afterAll(() => server.close())
