import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, totalCount, unwrap } from './client'
import type { paths } from './schema'
import type {
  Application,
  ApplicationInput,
  ApplicationPatch,
  ApplicationStatus,
  CompanyInput,
  CompanyPatch,
  InterviewInput,
  InterviewPatch,
} from './types'

export type ApplicationQuery = NonNullable<paths['/applications']['get']['parameters']['query']>
export type CompanyQuery = NonNullable<paths['/companies']['get']['parameters']['query']>
export type InterviewQuery = NonNullable<paths['/interviews']['get']['parameters']['query']>

export const keys = {
  me: ['me'] as const,
  applications: ['applications'] as const,
  application: (id: number) => ['applications', id] as const,
  companies: ['companies'] as const,
  company: (id: number) => ['companies', id] as const,
  board: ['applications', 'board'] as const,
  interviews: ['interviews'] as const,
  dashboard: ['dashboard'] as const,
}

// ---------------------------------------------------------------- applications

export function useApplications(query: ApplicationQuery) {
  return useQuery({
    queryKey: [...keys.applications, 'list', query],
    queryFn: async () => {
      const { data, response } = await unwrap(api.GET('/applications', { params: { query } }))
      return { items: data, total: totalCount(response) }
    },
    placeholderData: keepPreviousData,
  })
}

export function useApplication(id: number) {
  return useQuery({
    queryKey: keys.application(id),
    queryFn: async () =>
      (await unwrap(api.GET('/applications/{application_id}', { params: { path: { application_id: id } } }))).data,
  })
}

export function useCreateApplication() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (body: ApplicationInput) => (await unwrap(api.POST('/applications', { body }))).data.application,
    onSuccess: () => {
      invalidateApplicationData(client)
    },
  })
}

export function useUpdateApplication(id: number) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (body: ApplicationPatch) =>
      (await unwrap(api.PATCH('/applications/{application_id}', { params: { path: { application_id: id } }, body })))
        .data,
    onSuccess: (application) => {
      client.setQueryData(keys.application(id), application)
      invalidateApplicationData(client)
    },
  })
}

export function useDeleteApplication() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) =>
      unwrap(api.DELETE('/applications/{application_id}', { params: { path: { application_id: id } } })),
    onSuccess: () => {
      invalidateApplicationData(client)
    },
  })
}

// ------------------------------------------------------------------- companies

export function useCompanies(query: CompanyQuery = {}) {
  return useQuery({
    queryKey: [...keys.companies, 'list', query],
    queryFn: async () => {
      const { data, response } = await unwrap(api.GET('/companies', { params: { query } }))
      return { items: data, total: totalCount(response) }
    },
    placeholderData: keepPreviousData,
  })
}

export function useCompany(id: number) {
  return useQuery({
    queryKey: keys.company(id),
    queryFn: async () =>
      (await unwrap(api.GET('/companies/{company_id}', { params: { path: { company_id: id } } }))).data,
  })
}

export function useCreateCompany() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (body: CompanyInput) => (await unwrap(api.POST('/companies', { body }))).data,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.companies }),
  })
}

export function useUpdateCompany(id: number) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (body: CompanyPatch) =>
      (await unwrap(api.PATCH('/companies/{company_id}', { params: { path: { company_id: id } }, body }))).data,
    onSuccess: (company) => {
      client.setQueryData(keys.company(id), company)
      client.invalidateQueries({ queryKey: keys.companies })
    },
  })
}

export function useDeleteCompany() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) =>
      unwrap(api.DELETE('/companies/{company_id}', { params: { path: { company_id: id } } })),
    onSuccess: () => {
      invalidateApplicationData(client)
    },
  })
}

// Everything that depends on applications (lists, board, dashboard, companies' counts).
function invalidateApplicationData(client: ReturnType<typeof useQueryClient>) {
  client.invalidateQueries({ queryKey: keys.applications })
  client.invalidateQueries({ queryKey: keys.companies })
  client.invalidateQueries({ queryKey: keys.dashboard })
  client.invalidateQueries({ queryKey: keys.interviews })
}

// ---------------------------------------------------------------- dashboard

export function useDashboardStats() {
  return useQuery({
    queryKey: keys.dashboard,
    queryFn: async () => (await unwrap(api.GET('/dashboard/stats'))).data,
  })
}

// -------------------------------------------------------------------- board

const BOARD_PAGE = 100

/** All of the user's applications (the API pages at 100), for the Kanban board. */
export function useBoardApplications() {
  return useQuery({
    queryKey: keys.board,
    queryFn: async () => {
      const all: Application[] = []
      for (let offset = 0; ; offset += BOARD_PAGE) {
        const { data, response } = await unwrap(
          api.GET('/applications', { params: { query: { sort: '-updated_at', limit: BOARD_PAGE, offset } } }),
        )
        all.push(...data)
        if (all.length >= totalCount(response) || data.length === 0) return all
      }
    },
  })
}

/** Change an application's status with an optimistic update (rolled back on failure). */
export function useMoveApplication() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, status }: { id: number; status: ApplicationStatus }) =>
      (
        await unwrap(
          api.PATCH('/applications/{application_id}', { params: { path: { application_id: id } }, body: { status } }),
        )
      ).data,
    onMutate: async ({ id, status }) => {
      await client.cancelQueries({ queryKey: keys.board })
      const previous = client.getQueryData<Application[]>(keys.board)
      client.setQueryData<Application[]>(keys.board, (items) =>
        items?.map((item) => (item.id === id ? { ...item, status } : item)),
      )
      return { previous }
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) client.setQueryData(keys.board, context.previous)
    },
    onSettled: () => invalidateApplicationData(client),
  })
}

// --------------------------------------------------------------- interviews

export function useInterviews(query: InterviewQuery, enabled = true) {
  return useQuery({
    queryKey: [...keys.interviews, 'list', query],
    queryFn: async () => {
      const { data, response } = await unwrap(api.GET('/interviews', { params: { query } }))
      return { items: data, total: totalCount(response) }
    },
    placeholderData: keepPreviousData,
    enabled,
  })
}

export function useCreateInterview() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (body: InterviewInput) => (await unwrap(api.POST('/interviews', { body }))).data,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.interviews })
      client.invalidateQueries({ queryKey: keys.dashboard })
    },
  })
}

export function useUpdateInterview() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: InterviewPatch }) =>
      (await unwrap(api.PATCH('/interviews/{interview_id}', { params: { path: { interview_id: id } }, body }))).data,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.interviews })
      client.invalidateQueries({ queryKey: keys.dashboard })
    },
  })
}

export function useDeleteInterview() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) =>
      unwrap(api.DELETE('/interviews/{interview_id}', { params: { path: { interview_id: id } } })),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.interviews })
      client.invalidateQueries({ queryKey: keys.dashboard })
    },
  })
}

// ------------------------------------------------------------------ account

export function useUpdateProfile() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (full_name: string) => (await unwrap(api.PATCH('/users/me', { body: { full_name } }))).data,
    onSuccess: (user) => client.setQueryData(keys.me, user),
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (body: { current_password: string; new_password: string }) =>
      unwrap(api.POST('/users/me/password', { body })),
  })
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: async (password: string) => unwrap(api.DELETE('/users/me', { body: { password } })),
  })
}
