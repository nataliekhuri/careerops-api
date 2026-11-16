import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, totalCount, unwrap } from './client'
import type { paths } from './schema'
import type { ApplicationInput, ApplicationPatch, CompanyInput, CompanyPatch } from './types'

export type ApplicationQuery = NonNullable<paths['/applications']['get']['parameters']['query']>
export type CompanyQuery = NonNullable<paths['/companies']['get']['parameters']['query']>

export const keys = {
  me: ['me'] as const,
  applications: ['applications'] as const,
  application: (id: number) => ['applications', id] as const,
  companies: ['companies'] as const,
  company: (id: number) => ['companies', id] as const,
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
      client.invalidateQueries({ queryKey: keys.applications })
      client.invalidateQueries({ queryKey: keys.companies })
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
      client.invalidateQueries({ queryKey: keys.applications })
      client.invalidateQueries({ queryKey: keys.companies })
    },
  })
}

export function useDeleteApplication() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) =>
      unwrap(api.DELETE('/applications/{application_id}', { params: { path: { application_id: id } } })),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.applications })
      client.invalidateQueries({ queryKey: keys.companies })
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
      client.invalidateQueries({ queryKey: keys.companies })
      client.invalidateQueries({ queryKey: keys.applications })
    },
  })
}
