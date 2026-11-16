import { Navigate, Outlet, useLocation } from 'react-router'

import { FullPageSpinner } from '@/components/ui/Spinner'

import { useAuth } from './context'

/** Only renders its child routes for signed-in users; otherwise redirects to /login. */
export function RequireAuth() {
  const { user, isLoading, signedOutTo } = useAuth()
  const location = useLocation()

  if (isLoading) return <FullPageSpinner label="Checking your session" />
  // After a deliberate sign-out, go where the app asked; otherwise ask the user to sign in.
  if (!user && signedOutTo) return <Navigate to={signedOutTo} replace />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return <Outlet />
}

/** Sends signed-in users away from the login and register pages. */
export function RedirectIfAuthenticated() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <FullPageSpinner label="Checking your session" />
  if (user) return <Navigate to="/dashboard" replace />
  return <Outlet />
}
