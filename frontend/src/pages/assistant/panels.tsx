import { AlertTriangle, CalendarClock, Check, ChevronRight, Lightbulb, X } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'

import { useCvReview, useInterviewPrep, useJobAnalysis, useMatch } from '@/api/hooks'
import type { CvReviewRequest, JobSource, MatchedSkill, MatchResult, PrepQuestion } from '@/api/types'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { cn } from '@/lib/cn'
import { formatDateTime } from '@/lib/format'

const IMPORTANCE_LABEL = { required: 'Required', nice_to_have: 'Nice to have' } as const

function Loading({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-slate-500">
      <Spinner label={label} /> {label}…
    </div>
  )
}

function Heading({ children }: { children: ReactNode }) {
  return <h3 className="text-sm font-semibold text-slate-900">{children}</h3>
}

export function Warnings({ warnings, applicationId }: { warnings: string[]; applicationId?: number }) {
  if (warnings.length === 0) return null
  return (
    <div className="space-y-2" role="note" aria-label="Analysis warnings">
      {warnings.map((warning) => (
        <p key={warning} className="flex gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900 ring-1 ring-amber-200">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
          <span>
            {warning}{' '}
            {applicationId && warning.includes('no job description') && (
              <Link to={`/applications/${applicationId}`} className="font-medium underline underline-offset-2">
                Open the application
              </Link>
            )}
          </span>
        </p>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------- match

function scoreColor(score: number) {
  return score >= 75
    ? 'text-emerald-600'
    : score >= 55
      ? 'text-brand-600'
      : score >= 35
        ? 'text-amber-600'
        : 'text-rose-600'
}

function ScoreRing({ score, level }: { score: number; level: string }) {
  const circumference = 2 * Math.PI * 42
  return (
    <div className="flex items-center gap-4">
      <div className={cn('relative size-28 shrink-0', scoreColor(score))}>
        <svg viewBox="0 0 100 100" className="size-full -rotate-90" aria-hidden>
          <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="10" />
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - score / 100)}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-3xl font-semibold text-slate-900">
          {score}
        </span>
      </div>
      <div>
        <p className="text-sm text-slate-500">Match score</p>
        <p className="text-lg font-semibold text-slate-900">
          <span className="sr-only">{score} out of 100: </span>
          {level}
        </p>
      </div>
    </div>
  )
}

function SkillList({
  title,
  items,
  tone,
}: {
  title: string
  items: MatchedSkill[]
  tone: 'good' | 'partial' | 'missing'
}) {
  const styles = {
    good: { icon: Check, color: 'text-emerald-600' },
    partial: { icon: ChevronRight, color: 'text-amber-600' },
    missing: { icon: X, color: 'text-rose-600' },
  }[tone]
  const Icon = styles.icon
  return (
    <section aria-label={title}>
      <Heading>
        {title} <span className="font-normal text-slate-500">({items.length})</span>
      </Heading>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">None</p>
      ) : (
        <ul className="mt-2 space-y-1.5">
          {items.map((skill) => (
            <li key={skill.name} className="flex items-start gap-2 text-sm">
              <Icon className={cn('mt-0.5 size-4 shrink-0', styles.color)} aria-hidden />
              <span>
                <span className="font-medium text-slate-900">{skill.name}</span>{' '}
                <span className="text-xs text-slate-500">
                  · {IMPORTANCE_LABEL[skill.importance]} · {skill.reason}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export function MatchView({ result }: { result: MatchResult }) {
  if (result.score === null || result.score === undefined) {
    return (
      <div className="rounded-lg bg-slate-50 p-5 text-sm text-slate-700">
        <p className="font-medium text-slate-900">{result.level}</p>
        <p className="mt-1">{result.explanation[0]}</p>
        <Link
          to="/settings#career-profile"
          className="mt-3 inline-block font-medium text-brand-700 underline underline-offset-2"
        >
          Open your career profile
        </Link>
      </div>
    )
  }
  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <ScoreRing score={result.score} level={result.level} />
        <div className="space-y-3" aria-label="How the score is calculated">
          {result.components.map((component) => (
            <div key={component.name}>
              <div className="flex justify-between text-sm">
                <span className="font-medium text-slate-700">
                  {component.name} <span className="font-normal text-slate-500">({component.weight}% of score)</span>
                </span>
                <span className="text-slate-900">{Math.round(component.score)}%</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-100">
                <div className="h-2 rounded-full bg-brand-500" style={{ width: `${component.score}%` }} />
              </div>
              <p className="mt-1 text-xs text-slate-500">{component.detail}</p>
            </div>
          ))}
        </div>
      </div>
      <section aria-label="Why this score">
        <Heading>Why this score</Heading>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
          {result.explanation.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </section>
      <div className="grid gap-6 md:grid-cols-3">
        <SkillList title="You have" items={result.matched} tone="good" />
        <SkillList title="Related experience" items={result.partial} tone="partial" />
        <SkillList title="Missing" items={result.missing} tone="missing" />
      </div>
      <section aria-label="Recommendations" className="rounded-lg bg-brand-50/60 p-4">
        <Heading>What to do next</Heading>
        <ul className="mt-2 space-y-1.5 text-sm text-slate-700">
          {result.recommendations.map((tip) => (
            <li key={tip} className="flex gap-2">
              <Lightbulb className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden />
              {tip}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

export function MatchPanel({ source }: { source: JobSource }) {
  const match = useMatch(source)
  if (match.error) return <ErrorMessage error={match.error} onRetry={() => match.refetch()} />
  if (match.isPending) return <Loading label="Scoring the match" />
  return (
    <div className="space-y-5">
      <Warnings warnings={match.data.job.warnings} applicationId={source.application_id ?? undefined} />
      <MatchView result={match.data} />
    </div>
  )
}

// ---------------------------------------------------------------- job analysis

export function AnalysisPanel({ source }: { source: JobSource }) {
  const analysis = useJobAnalysis(source)
  if (analysis.error) return <ErrorMessage error={analysis.error} onRetry={() => analysis.refetch()} />
  if (analysis.isPending) return <Loading label="Analysing the job" />
  const job = analysis.data
  const facts = [
    ['Role', job.role_family],
    ['Seniority', job.seniority],
    ['Experience', job.min_years_experience ? `${job.min_years_experience}+ years` : 'Not specified'],
    ['Work mode', job.work_modes.length ? job.work_modes.join(', ') : 'Not specified'],
  ] as const
  return (
    <div className="space-y-6">
      <Warnings warnings={job.warnings} applicationId={source.application_id ?? undefined} />
      <p className="text-sm text-slate-700">{job.summary}</p>
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {facts.map(([label, value]) => (
          <div key={label} className="rounded-lg bg-slate-50 p-3">
            <dt className="text-xs text-slate-500">{label}</dt>
            <dd className="mt-0.5 text-sm font-medium text-slate-900 capitalize">{value}</dd>
          </div>
        ))}
      </dl>
      {job.skills.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <caption className="sr-only">Skills found in the job description</caption>
            <thead className="text-xs tracking-wide text-slate-500 uppercase">
              <tr>
                <th scope="col" className="py-2 pr-4 font-medium">
                  Skill
                </th>
                <th scope="col" className="py-2 pr-4 font-medium">
                  Importance
                </th>
                <th scope="col" className="hidden py-2 pr-4 font-medium sm:table-cell">
                  Category
                </th>
                <th scope="col" className="hidden py-2 font-medium md:table-cell">
                  Found in
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {job.skills.map((skill) => (
                <tr key={skill.name}>
                  <td className="py-2 pr-4 font-medium text-slate-900">{skill.name}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-xs font-medium',
                        skill.importance === 'required' ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-600',
                      )}
                    >
                      {IMPORTANCE_LABEL[skill.importance]}
                    </span>
                  </td>
                  <td className="hidden py-2 pr-4 text-slate-600 sm:table-cell">{skill.category}</td>
                  <td className="hidden max-w-md truncate py-2 text-slate-500 md:table-cell" title={skill.evidence}>
                    {skill.evidence}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------- CV review

const PRIORITY_STYLE = {
  high: 'bg-rose-50 text-rose-700',
  medium: 'bg-amber-50 text-amber-800',
  low: 'bg-slate-100 text-slate-600',
} as const

export function CvPanel({ source }: { source: JobSource }) {
  const request: CvReviewRequest = source.application_id
    ? { application_id: source.application_id }
    : { job_description: source.job_description, position: source.position }
  const review = useCvReview(request)
  if (review.error) return <ErrorMessage error={review.error} onRetry={() => review.refetch()} />
  if (review.isPending) return <Loading label="Reviewing your CV" />
  const data = review.data
  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-500">
        Reviews the CV saved in your{' '}
        <Link to="/settings#career-profile" className="font-medium text-brand-700 underline underline-offset-2">
          career profile
        </Link>
        , tailored to this job.
      </p>
      {data.score !== null && data.score !== undefined && (
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <p className="text-sm text-slate-500">Checks passed</p>
            <p className={cn('text-3xl font-semibold', scoreColor(data.score))}>{data.score}%</p>
            {data.keyword_coverage && (
              <div className="mt-4">
                <p className="text-sm font-medium text-slate-700">
                  Job keywords in your CV: {data.keyword_coverage.percent}%
                </p>
                <div className="mt-1 h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-brand-500"
                    style={{ width: `${data.keyword_coverage.percent}%` }}
                  />
                </div>
                {data.keyword_coverage.missing.length > 0 && (
                  <p className="mt-1 text-xs text-slate-500">Missing: {data.keyword_coverage.missing.join(', ')}</p>
                )}
              </div>
            )}
          </div>
          <ul className="space-y-1.5 text-sm" aria-label="CV checks">
            {data.checks.map((check) => (
              <li key={check.name} className="flex gap-2">
                {check.passed ? (
                  <Check className="mt-0.5 size-4 shrink-0 text-emerald-600" aria-label="Passed" />
                ) : (
                  <X className="mt-0.5 size-4 shrink-0 text-rose-600" aria-label="Needs work" />
                )}
                <span>
                  <span className="font-medium text-slate-900">{check.name}</span>{' '}
                  <span className="text-slate-500">· {check.detail}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <section aria-label="Suggestions">
        <Heading>Suggestions</Heading>
        <ul className="mt-3 space-y-3">
          {data.suggestions.map((suggestion) => (
            <li key={suggestion.title}>
              <Card className="p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      'rounded-full px-2 py-0.5 text-xs font-medium capitalize',
                      PRIORITY_STYLE[suggestion.priority],
                    )}
                  >
                    {suggestion.priority} priority
                  </span>
                  <span className="text-xs text-slate-500">{suggestion.category}</span>
                </div>
                <p className="mt-2 font-medium text-slate-900">{suggestion.title}</p>
                <p className="mt-1 text-sm text-slate-600">{suggestion.detail}</p>
                {suggestion.example && (
                  <p className="mt-2 rounded bg-slate-50 p-2 text-xs text-slate-600">{suggestion.example}</p>
                )}
              </Card>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

// ---------------------------------------------------------------- interview prep

function QuestionList({ title, questions }: { title: string; questions: PrepQuestion[] }) {
  if (questions.length === 0) return null
  return (
    <section aria-label={title}>
      <Heading>{title}</Heading>
      <ul className="mt-2 divide-y divide-slate-100 rounded-lg ring-1 ring-slate-200">
        {questions.map((q) => (
          <li key={q.question}>
            <details className="group p-3">
              <summary className="cursor-pointer list-none text-sm text-slate-900 marker:hidden">
                <span className="flex items-start gap-2">
                  <ChevronRight
                    className="mt-0.5 size-4 shrink-0 text-slate-400 transition-transform group-open:rotate-90"
                    aria-hidden
                  />
                  <span>
                    {q.question} <span className="text-xs text-slate-500">· {q.topic}</span>
                  </span>
                </span>
              </summary>
              <p className="mt-2 ml-6 text-sm text-slate-600">
                <span className="font-medium text-slate-700">Tip:</span> {q.tip}
              </p>
            </details>
          </li>
        ))}
      </ul>
    </section>
  )
}

function BulletList({ title, items }: { title: string; items: string[] }) {
  return (
    <section aria-label={title}>
      <Heading>{title}</Heading>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  )
}

export function PrepPanel({ source }: { source: JobSource }) {
  const prep = useInterviewPrep(source)
  if (prep.error) return <ErrorMessage error={prep.error} onRetry={() => prep.refetch()} />
  if (prep.isPending) return <Loading label="Preparing interview questions" />
  const data = prep.data
  return (
    <div className="space-y-6">
      {data.upcoming_interviews.length > 0 && (
        <section aria-label="Upcoming interviews" className="rounded-lg bg-brand-50/60 p-4">
          <Heading>Your upcoming interviews</Heading>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {data.upcoming_interviews.map((interview) => (
              <li key={interview.id} className="flex items-center gap-2">
                <CalendarClock className="size-4 text-brand-600" aria-hidden />
                {formatDateTime(interview.scheduled_at)} ·{' '}
                <span className="capitalize">{interview.interview_type}</span>
                {interview.interviewer && ` · ${interview.interviewer}`}
              </li>
            ))}
          </ul>
        </section>
      )}
      {data.focus_skills.length > 0 && (
        <div>
          <Heading>Focus skills</Heading>
          <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Focus skills">
            {data.focus_skills.map((skill) => (
              <li key={skill} className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">
                {skill}
              </li>
            ))}
          </ul>
        </div>
      )}
      <QuestionList title="Technical questions" questions={data.technical_questions} />
      <QuestionList title="Your gaps: be ready for these" questions={data.gap_questions} />
      <QuestionList title="Behavioural questions" questions={data.behavioral_questions} />
      <div className="grid gap-6 md:grid-cols-2">
        <BulletList title="Questions to ask them" items={data.questions_to_ask} />
        <BulletList title="Company research" items={data.company_research} />
      </div>
      <BulletList title="Tips" items={data.tips} />
    </div>
  )
}
