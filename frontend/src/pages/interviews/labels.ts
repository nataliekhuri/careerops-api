/** Human-readable names for interview types and outcomes. */
const LABELS: Record<string, string> = {
  video: 'Video call',
  phone: 'Phone',
  onsite: 'On-site',
  technical: 'Technical',
  behavioral: 'Behavioral',
  other: 'Other',
  pending: 'Pending',
  passed: 'Passed',
  failed: 'Not successful',
  cancelled: 'Cancelled',
}
export const label = (value: string) => LABELS[value] ?? value
