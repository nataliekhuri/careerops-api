import { createContext, useContext } from 'react'

import type { User, UserInput } from '@/api/types'

export interface AuthState {
  user: User | null
  /** True while we don't yet know whether a stored token is still valid. */
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (input: UserInput) => Promise<void>
  /** Sign out. `to` is where protected pages send the user afterwards (default: /login). */
  logout: (to?: string) => void
  /** Where to go after a deliberate sign-out, or null for the default. */
  signedOutTo: string | null
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
