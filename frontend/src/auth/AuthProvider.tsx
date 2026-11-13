import { useQuery, useQueryClient } from '@tanstack/react-query'
import { type ReactNode, useCallback, useEffect, useMemo, useState, useSyncExternalStore } from 'react'

import { api, unwrap } from '@/api/client'
import { keys } from '@/api/hooks'
import type { UserInput } from '@/api/types'

import { AuthContext, type AuthState } from './context'
import { clearToken, getToken, onTokenChange, setToken } from './token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const token = useSyncExternalStore(onTokenChange, getToken, () => null)
  const [signedOutTo, setSignedOutTo] = useState<string | null>(null)

  const me = useQuery({
    queryKey: keys.me,
    queryFn: async () => (await unwrap(api.GET('/users/me'))).data,
    enabled: token !== null,
    retry: false,
    staleTime: 5 * 60_000,
  })

  // Signed out (logout, expiry or a 401 anywhere): drop all cached private data.
  useEffect(() => {
    if (token === null) queryClient.clear()
  }, [token, queryClient])

  const login = useCallback(
    async (email: string, password: string) => {
      const { data } = await unwrap(
        api.POST('/auth/login', {
          body: { username: email, password, scope: '' },
          bodySerializer: (body) => new URLSearchParams(body as Record<string, string>),
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }),
      )
      queryClient.clear()
      setSignedOutTo(null)
      setToken(data.access_token)
    },
    [queryClient],
  )

  const register = useCallback(
    async (input: UserInput) => {
      await unwrap(api.POST('/auth/register', { body: input }))
      await login(input.email, input.password)
    },
    [login],
  )

  const logout = useCallback((to?: string) => {
    setSignedOutTo(to ?? null)
    clearToken()
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      user: token ? (me.data ?? null) : null,
      isLoading: token !== null && me.isPending,
      login,
      register,
      logout,
      signedOutTo,
    }),
    [token, me.data, me.isPending, login, register, logout, signedOutTo],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
