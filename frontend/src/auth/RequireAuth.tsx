import { Navigate, Outlet, useLocation } from 'react-router'

import { FullPageSpinner } from '@/components/ui/Spinner'

import { useAuth } from './context'

/** Only renders its child routes for signed-in users; otherwise redirects to /login. */
export function RequireAuth() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <FullPageSpinner label="Checking your session" />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return <Outlet />
}

/** Sends signed-in users away from the login and register pages. */
export function RedirectIfAuthenticated() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <FullPageSpinner label="Checking your session" />
  if (user) return <Navigate to="/applications" replace />
  return <Outlet />
}
