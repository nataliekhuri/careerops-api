import '@testing-library/jest-dom/vitest'

import { cleanup, configure } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'

import { server } from './server'

// CI machines can be slow on the first render; wait up to 3 s for async UI.
configure({ asyncUtilTimeout: 3000 })

// Any request without a matching mock fails the test, so nothing reaches a real network.
beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  localStorage.clear()
})
afterAll(() => server.close())
