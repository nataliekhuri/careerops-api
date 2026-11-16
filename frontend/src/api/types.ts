import type { components } from './schema'

type Schemas = components['schemas']

export type Application = Schemas['ApplicationRead']
export type ApplicationInput = Schemas['JobApplication']
export type ApplicationPatch = Schemas['ApplicationUpdate']
export type ApplicationStatus = Schemas['ApplicationStatus']
export type ApplicationSort = Schemas['SortField']
export type Company = Schemas['CompanyRead']
export type CompanyInput = Schemas['CompanyCreate']
export type CompanyPatch = Schemas['CompanyUpdate']
export type CompanySort = Schemas['CompanySort']
export type User = Schemas['UserRead']
export type UserInput = Schemas['UserCreate']

export const APPLICATION_STATUSES = [
  'Applied',
  'Screening',
  'Interview',
  'Offer',
  'Rejected',
  'Withdrawn',
] as const satisfies readonly ApplicationStatus[]
