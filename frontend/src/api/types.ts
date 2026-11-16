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
export type Interview = Schemas['InterviewRead']
export type InterviewInput = Schemas['InterviewCreate']
export type InterviewPatch = Schemas['InterviewUpdate']
export type InterviewType = Schemas['InterviewType']
export type InterviewOutcome = Schemas['InterviewOutcome']
export type DashboardStats = Schemas['DashboardStats']

export const APPLICATION_STATUSES = [
  'Applied',
  'Screening',
  'Interview',
  'Offer',
  'Rejected',
  'Withdrawn',
] as const satisfies readonly ApplicationStatus[]

export const INTERVIEW_TYPES = [
  'video',
  'phone',
  'onsite',
  'technical',
  'behavioral',
  'other',
] as const satisfies readonly InterviewType[]

export const INTERVIEW_OUTCOMES = [
  'pending',
  'passed',
  'failed',
  'cancelled',
] as const satisfies readonly InterviewOutcome[]
