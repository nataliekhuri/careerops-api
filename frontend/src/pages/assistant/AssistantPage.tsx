import { Lock, Sparkles } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { useAiProvider, useApplications, useCareerProfile, useSkillInsights } from '@/api/hooks'
import type { JobSource } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Button } from '@/components/ui/Button'
import { Card, PageHeader } from '@/components/ui/Card'
import { Field, Input, Select, Textarea } from '@/components/ui/Field'
import { Spinner } from '@/components/ui/Spinner'
import { Tabs } from '@/components/ui/Tabs'
import { cn } from '@/lib/cn'

import { AnalysisPanel, CvPanel, MatchPanel, PrepPanel } from './panels'

const TABS = [
  { id: 'match', label: 'Match score' },
  { id: 'analysis', label: 'Job analysis' },
  { id: 'cv', label: 'CV suggestions' },
  { id: 'prep', label: 'Interview prep' },
] as const
type Tab = (typeof TABS)[number]['id']
const isTab = (value: string | null): value is Tab => TABS.some((tab) => tab.id === value)

const MIN_PASTE = 30

function SourceForm({
  initialApplication,
  onAnalyse,
}: {
  initialApplication: string
  onAnalyse: (s: JobSource) => void
}) {
  const applications = useApplications({ limit: 100, sort: '-updated_at' })
  const [mode, setMode] = useState<'saved' | 'paste'>('saved')
  const [applicationId, setApplicationId] = useState(initialApplication)
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [error, setError] = useState<string | null>(null)

  function submit(event: FormEvent) {
    event.preventDefault()
    if (mode === 'saved') {
      if (!applicationId) return setError('Choose an application')
      setError(null)
      onAnalyse({ application_id: Number(applicationId) })
    } else {
      if (text.trim().length < MIN_PASTE)
        return setError(`Paste the job description (at least ${MIN_PASTE} characters)`)
      if (text.length > 20000) return setError('Use at most 20,000 characters')
      setError(null)
      onAnalyse({ job_description: text.trim(), position: title.trim() || null })
    }
  }

  const items = applications.data?.items ?? []
  return (
    <form onSubmit={submit} noValidate className="space-y-4" aria-label="Choose a job">
      <fieldset>
        <legend className="text-sm font-medium text-slate-700">Job to analyse</legend>
        <div className="mt-2 inline-flex rounded-lg bg-slate-100 p-1 text-sm">
          {(
            [
              ['saved', 'Saved application'],
              ['paste', 'Paste a job description'],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className={cn(
                'cursor-pointer rounded-md px-3 py-1.5 font-medium has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-brand-500',
                mode === value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500',
              )}
            >
              <input
                type="radio"
                name="source"
                value={value}
                checked={mode === value}
                onChange={() => {
                  setMode(value)
                  setError(null)
                }}
                className="sr-only"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      {mode === 'saved' ? (
        <Field
          label="Application"
          error={mode === 'saved' ? (error ?? undefined) : undefined}
          hint={
            items.length === 0 && !applications.isPending
              ? 'You have no applications yet. Paste a job description instead.'
              : 'Applications with a saved job description give the best results.'
          }
        >
          {(props) => (
            <Select
              {...props}
              value={applicationId}
              onChange={(e) => setApplicationId(e.target.value)}
              disabled={applications.isPending}
            >
              <option value="">Choose an application…</option>
              {items.map((application) => (
                <option key={application.id} value={application.id}>
                  {application.company} — {application.position}
                  {application.job_description ? '' : ' (no job description)'}
                </option>
              ))}
            </Select>
          )}
        </Field>
      ) : (
        <div className="grid gap-4">
          <Field label="Job title (optional)">
            {(props) => <Input {...props} value={title} onChange={(e) => setTitle(e.target.value)} />}
          </Field>
          <Field
            label="Job description"
            error={error ?? undefined}
            hint={`${text.length.toLocaleString()} / 20,000 characters`}
          >
            {(props) => <Textarea rows={8} {...props} value={text} onChange={(e) => setText(e.target.value)} />}
          </Field>
        </div>
      )}
      {applications.error && <ErrorMessage error={applications.error} onRetry={() => applications.refetch()} />}
      <div className="flex justify-end">
        <Button type="submit">
          <Sparkles className="size-4" aria-hidden /> Analyse
        </Button>
      </div>
    </form>
  )
}

function SkillInsightsCard() {
  const insights = useSkillInsights()
  return (
    <Card className="p-5">
      <h2 className="text-base font-semibold text-slate-900">Skills your applications ask for</h2>
      {insights.error ? (
        <div className="mt-3">
          <ErrorMessage error={insights.error} onRetry={() => insights.refetch()} />
        </div>
      ) : insights.isPending ? (
        <div className="mt-4">
          <Spinner label="Loading skill insights" />
        </div>
      ) : insights.data.analyzed_applications === 0 ? (
        <p className="mt-2 text-sm text-slate-500">
          Add job descriptions to your applications to see which skills are most in demand.
        </p>
      ) : (
        <>
          <p className="mt-1 text-sm text-slate-500">
            From {insights.data.analyzed_applications} of {insights.data.total_applications} applications
            {insights.data.coverage_percent !== null && insights.data.coverage_percent !== undefined && (
              <>
                {' '}
                · you cover <span className="font-medium text-slate-900">{insights.data.coverage_percent}%</span>
              </>
            )}
          </p>
          <ul className="mt-4 space-y-2" aria-label="Most requested skills">
            {insights.data.skills.slice(0, 10).map((skill) => {
              const max = insights.data.skills[0]!.applications
              return (
                <li key={skill.name} className="text-sm">
                  <div className="flex justify-between">
                    <span className={cn('font-medium', skill.have ? 'text-slate-900' : 'text-rose-700')}>
                      {skill.name}
                      <span className="sr-only">{skill.have ? ' (you have it)' : ' (missing)'}</span>
                    </span>
                    <span className="text-slate-500">{skill.applications}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-slate-100">
                    <div
                      className={cn('h-1.5 rounded-full', skill.have ? 'bg-emerald-500' : 'bg-rose-400')}
                      style={{ width: `${(100 * skill.applications) / max}%` }}
                    />
                  </div>
                </li>
              )
            })}
          </ul>
          {insights.data.top_missing.length > 0 && (
            <p className="mt-4 text-sm text-slate-700">
              <span className="font-medium">Worth learning next:</span>{' '}
              {insights.data.top_missing.slice(0, 3).join(', ')}
            </p>
          )}
        </>
      )}
    </Card>
  )
}

function ProfileHint() {
  const profile = useCareerProfile()
  if (!profile.data || profile.data.skills.length > 0 || profile.data.cv_text) return null
  return (
    <p className="rounded-lg bg-brand-50 p-3 text-sm text-brand-900 ring-1 ring-brand-200">
      Add your skills and CV in your{' '}
      <Link to="/settings#career-profile" className="font-medium underline underline-offset-2">
        career profile
      </Link>{' '}
      to get match scores and tailored CV suggestions.
    </p>
  )
}

export function AssistantPage() {
  const [params, setParams] = useSearchParams()
  const provider = useAiProvider()
  const initialApplication = params.get('application') ?? ''
  const [source, setSource] = useState<JobSource | null>(() =>
    /^\d+$/.test(initialApplication) ? { application_id: Number(initialApplication) } : null,
  )
  const tabParam = params.get('tab')
  const tab: Tab = isTab(tabParam) ? tabParam : 'match'

  function changeTab(next: Tab) {
    const updated = new URLSearchParams(params)
    updated.set('tab', next)
    setParams(updated, { replace: true })
  }

  function analyse(next: JobSource) {
    setSource(next)
    const updated = new URLSearchParams(params)
    if (next.application_id) updated.set('application', String(next.application_id))
    else updated.delete('application')
    setParams(updated, { replace: true })
  }

  return (
    <>
      <PageHeader
        title="AI assistant"
        description="Analyse a job, see how well you match, improve your CV and prepare for the interview."
      />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <ProfileHint />
          <Card className="p-5">
            <SourceForm initialApplication={initialApplication} onAnalyse={analyse} />
          </Card>
          {source && (
            <Card className="p-5">
              <Tabs label="Assistant results" items={TABS} value={tab} onChange={changeTab}>
                {tab === 'match' && <MatchPanel source={source} />}
                {tab === 'analysis' && <AnalysisPanel source={source} />}
                {tab === 'cv' && <CvPanel source={source} />}
                {tab === 'prep' && <PrepPanel source={source} />}
              </Tabs>
            </Card>
          )}
        </div>
        <div className="space-y-6">
          <SkillInsightsCard />
          {provider.data && (
            <p className="flex gap-2 text-xs text-slate-500">
              <Lock className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              {provider.data.description}
            </p>
          )}
        </div>
      </div>
    </>
  )
}
