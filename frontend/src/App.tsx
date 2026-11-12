import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router'

import { RedirectIfAuthenticated, RequireAuth } from '@/auth/RequireAuth'
import { FullPageSpinner } from '@/components/ui/Spinner'
import { Landing } from '@/pages/Landing'
import { NotFound } from '@/pages/NotFound'

// Each area is loaded only when first visited, keeping the initial download small.
const AppLayout = lazy(() => import('@/layouts/AppLayout').then((m) => ({ default: m.AppLayout })))
const LoginPage = lazy(() => import('@/pages/AuthPages').then((m) => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('@/pages/AuthPages').then((m) => ({ default: m.RegisterPage })))
const ApplicationsPage = lazy(() =>
  import('@/pages/applications/ApplicationsPage').then((m) => ({ default: m.ApplicationsPage })),
)
const ApplicationDetailPage = lazy(() =>
  import('@/pages/applications/ApplicationDetailPage').then((m) => ({ default: m.ApplicationDetailPage })),
)
const NewApplicationPage = lazy(() =>
  import('@/pages/applications/ApplicationDetailPage').then((m) => ({ default: m.NewApplicationPage })),
)
const CompaniesPage = lazy(() => import('@/pages/companies/CompaniesPage').then((m) => ({ default: m.CompaniesPage })))
const CompanyDetailPage = lazy(() =>
  import('@/pages/companies/CompanyDetailPage').then((m) => ({ default: m.CompanyDetailPage })),
)

export function App() {
  return (
    <Suspense fallback={<FullPageSpinner label="Loading" />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<RedirectIfAuthenticated />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/applications/new" element={<NewApplicationPage />} />
            <Route path="/applications/:id" element={<ApplicationDetailPage />} />
            <Route path="/companies" element={<CompaniesPage />} />
            <Route path="/companies/:id" element={<CompanyDetailPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}
