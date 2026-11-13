// Load the lazily routed page while the file is collected, so the first test measures
// behaviour rather than cold module compilation.
import '@/pages/assistant/AssistantPage'
import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, test } from 'vitest'

import type { CvReview, InterviewPrep, JobAnalysis, MatchResult } from '@/api/types'
import { renderApp } from '@/test/render'
import { API, emptyInsights, makeApplication, makeCareerProfile, server, signedIn } from '@/test/server'

const APPS = [
  makeApplication({ id: 4, company: 'Northwind', position: 'Backend Engineer', job_description: 'Python...' }),
  makeApplication({ id: 5, company: 'Globex', position: 'Data Engineer' }),
]
const PROFILE = makeCareerProfile({ skills: ['Python'], recognized_skills: ['Python'] })

const JOB: JobAnalysis = {
  title: 'Backend Engineer',
  role_family: 'backend',
  seniority: 'Senior',
  min_years_experience: 5,
  work_modes: ['remote'],
  skills: [
    { name: 'Python', category: 'Languages', importance: 'required', mentions: 2, evidence: '5+ years of Python' },
    { name: 'Kafka', category: 'Cloud & DevOps', importance: 'nice_to_have', mentions: 1, evidence: 'Kafka is a plus' },
  ],
  required_skills: ['Python'],
  nice_to_have_skills: ['Kafka'],
  summary: 'Senior backend role; core skills Python; 5+ years of experience; remote.',
  word_count: 120,
  warnings: [],
}

const MATCH: MatchResult = {
  score: 82,
  level: 'Strong match',
  components: [
    { name: 'Skills', weight: 85, score: 85, detail: '5 matched, 1 related, 1 missing' },
    { name: 'Experience', weight: 15, score: 60, detail: 'You have 3 years; the job asks for 5+' },
  ],
  matched: [
    { name: 'Python', category: 'Languages', importance: 'required', credit: 1, reason: 'In your career profile' },
  ],
  partial: [
    {
      name: 'PostgreSQL',
      category: 'Databases',
      importance: 'required',
      credit: 0.5,
      reason: 'Related experience: MySQL',
    },
  ],
  missing: [
    { name: 'AWS', category: 'Cloud & DevOps', importance: 'required', credit: 0, reason: 'Not in your profile or CV' },
  ],
  explanation: ['You cover 5 of 7 required skills.', 'Missing required: AWS.'],
  recommendations: ['Close the biggest gap first: AWS.'],
  job: JOB,
}

const CV: CvReview = {
  score: 60,
  word_count: 320,
  sections_found: ['Experience', 'Skills'],
  checks: [
    { name: 'Length', passed: true, detail: '320 words' },
    { name: 'Measurable results', passed: false, detail: '1 of 6 statements include a number' },
  ],
  keyword_coverage: { percent: 50, present: ['Python'], missing: ['AWS'] },
  suggestions: [
    {
      category: 'Impact',
      priority: 'high',
      title: 'Quantify your achievements',
      detail: 'Add numbers.',
      example: '“Built the API” → add the result',
    },
  ],
}

const PREP: InterviewPrep = {
  title: 'Backend Engineer',
  company: 'Northwind',
  role_family: 'backend',
  seniority: 'Senior',
  focus_skills: ['Python', 'AWS'],
  technical_questions: [
    { question: 'How do indexes work in PostgreSQL?', topic: 'PostgreSQL', tip: 'Mention EXPLAIN.' },
  ],
  behavioral_questions: [
    { question: 'Tell me about a project you are proud of.', topic: 'Behavioural (STAR)', tip: 'Pick one.' },
  ],
  gap_questions: [
    { question: 'You have not listed AWS. How would you get productive?', topic: 'AWS', tip: 'Be honest.' },
  ],
  questions_to_ask: ['What does success look like?'],
  company_research: ["Read Northwind's website"],
  tips: ['Technical round: think out loud.'],
  upcoming_interviews: [
    { id: 3, scheduled_at: '2026-11-20T09:00:00Z', interview_type: 'technical', interviewer: 'Priya' },
  ],
}

function json<T>(value: T, record?: (body: unknown) => void) {
  return async ({ request }: { request: Request }) => {
    record?.(await request.json())
    return HttpResponse.json(value as object)
  }
}

describe('AI assistant', () => {
  test('scores a saved application against the career profile', async () => {
    signedIn({ applications: APPS, careerProfile: PROFILE })
    let body: unknown
    server.use(
      http.post(
        `${API}/ai/match`,
        json(MATCH, (b) => (body = b)),
      ),
    )
    const { user } = renderApp('/assistant')

    await screen.findByRole('option', { name: 'Northwind — Backend Engineer' })
    expect(screen.getByRole('option', { name: 'Globex — Data Engineer (no job description)' })).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Application'), 'Northwind — Backend Engineer')
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    expect(await screen.findByText('Strong match')).toBeInTheDocument()
    expect(body).toEqual({ application_id: 4 })
    expect(screen.getByText('82')).toBeInTheDocument()
    const missing = screen.getByRole('region', { name: 'Missing' })
    expect(within(missing).getByText('AWS')).toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'Related experience' })).getByText(/MySQL/)).toBeInTheDocument()
    expect(screen.getByText('Close the biggest gap first: AWS.')).toBeInTheDocument()
    expect(screen.getByText('(15% of score)')).toBeInTheDocument()
  })

  test('opens straight into interview prep from an application link', async () => {
    signedIn({ applications: APPS, careerProfile: PROFILE })
    let body: unknown
    server.use(
      http.post(
        `${API}/ai/interview-prep`,
        json(PREP, (b) => (body = b)),
      ),
    )
    const { user } = renderApp('/assistant?application=4&tab=prep')

    const question = await screen.findByText('How do indexes work in PostgreSQL?')
    expect(body).toEqual({ application_id: 4 })
    expect(screen.getByRole('tab', { name: 'Interview prep' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('You have not listed AWS. How would you get productive?')).toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'Upcoming interviews' })).getByText(/Priya/)).toBeInTheDocument()

    expect(screen.getByText('Mention EXPLAIN.')).not.toBeVisible()
    await user.click(question)
    expect(screen.getByText('Mention EXPLAIN.')).toBeVisible()
  })

  test('analyses a pasted job description and validates it first', async () => {
    signedIn({ careerProfile: PROFILE })
    let body: unknown
    server.use(
      http.post(`${API}/ai/match`, json(MATCH)),
      http.post(
        `${API}/ai/job-analysis`,
        json(JOB, (b) => (body = b)),
      ),
    )
    const { user } = renderApp('/assistant?tab=analysis')

    await user.click(await screen.findByRole('radio', { name: 'Paste a job description' }))
    await user.type(screen.getByLabelText('Job description'), 'Too short')
    await user.click(screen.getByRole('button', { name: 'Analyse' }))
    expect(screen.getByText(/at least 30 characters/)).toBeInTheDocument()

    await user.type(screen.getByLabelText('Job title (optional)'), 'Backend Engineer')
    await user.type(screen.getByLabelText('Job description'), ' - we need Python and Kafka experience')
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    expect(await screen.findByText(JOB.summary)).toBeInTheDocument()
    expect(body).toEqual({
      job_description: 'Too short - we need Python and Kafka experience',
      position: 'Backend Engineer',
    })
    const table = screen.getByRole('table')
    expect(within(table).getByText('Kafka')).toBeInTheDocument()
    expect(within(table).getByText('Nice to have')).toBeInTheDocument()
  })

  test('tabs work with the keyboard and load their own data', async () => {
    signedIn({ applications: APPS, careerProfile: PROFILE })
    server.use(
      http.post(`${API}/ai/match`, json(MATCH)),
      http.post(`${API}/ai/cv-review`, json(CV)),
      http.post(`${API}/ai/interview-prep`, json(PREP)),
    )
    const { user } = renderApp('/assistant?application=4')

    const matchTab = await screen.findByRole('tab', { name: 'Match score' })
    await screen.findByText('Strong match')
    matchTab.focus()
    await user.keyboard('{End}{ArrowLeft}') // last tab (Interview prep), then back one (CV suggestions)

    const cvTab = screen.getByRole('tab', { name: 'CV suggestions' })
    expect(cvTab).toHaveAttribute('aria-selected', 'true')
    expect(cvTab).toHaveFocus()
    expect(await screen.findByText('Quantify your achievements')).toBeInTheDocument()
    expect(screen.getByText('Job keywords in your CV: 50%')).toBeInTheDocument()
    expect(screen.getByLabelText('Needs work')).toBeInTheDocument()
  })

  test('explains what is missing when there is no profile yet', async () => {
    signedIn({ applications: APPS })
    server.use(
      http.post(
        `${API}/ai/match`,
        json({
          ...MATCH,
          score: null,
          level: 'Not enough information',
          components: [],
          explanation: ['Add your skills or CV in Settings → Career profile to get a match score.'],
        }),
      ),
    )
    renderApp('/assistant?application=4')

    expect(await screen.findByText('Not enough information')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open your career profile' })).toHaveAttribute(
      'href',
      '/settings#career-profile',
    )
    expect(screen.getByRole('link', { name: 'career profile' })).toBeInTheDocument() // the page hint
  })

  test('warns when the application has no job description', async () => {
    signedIn({ applications: APPS, careerProfile: PROFILE })
    server.use(
      http.post(
        `${API}/ai/match`,
        json({ ...MATCH, job: { ...JOB, warnings: ['This application has no job description yet, so only...'] } }),
      ),
    )
    renderApp('/assistant?application=5')

    expect(await screen.findByText(/no job description yet/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open the application' })).toHaveAttribute('href', '/applications/5')
  })

  test('shows an API error with a retry', async () => {
    signedIn({ applications: APPS, careerProfile: PROFILE })
    let calls = 0
    server.use(
      http.post(`${API}/ai/match`, () => {
        calls += 1
        return HttpResponse.json(
          { detail: [{ type: 'not_found', loc: ['body', 'application_id'], msg: 'Application not found' }] },
          { status: 422 },
        )
      }),
    )
    const { user } = renderApp('/assistant?application=999')

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Application not found')
    await user.click(within(alert).getByRole('button', { name: 'Try again' }))
    await waitFor(() => expect(calls).toBe(2))
  })

  test('skill insights show demand and gaps across applications', async () => {
    signedIn({
      applications: APPS,
      careerProfile: PROFILE,
      insights: emptyInsights({
        analyzed_applications: 3,
        total_applications: 5,
        coverage_percent: 40,
        skills: [
          { name: 'Python', category: 'Languages', applications: 3, have: true },
          { name: 'AWS', category: 'Cloud & DevOps', applications: 2, have: false },
        ],
        top_missing: ['AWS'],
      }),
    })
    renderApp('/assistant')

    const list = await screen.findByRole('list', { name: 'Most requested skills' })
    expect(within(list).getByText('(missing)')).toBeInTheDocument()
    expect(screen.getByText(/From 3 of 5 applications/)).toBeInTheDocument()
    expect(screen.getByText('40%')).toBeInTheDocument()
    expect(screen.getByText('Worth learning next:')).toBeInTheDocument()
    expect(screen.getByText(/your data is not sent anywhere/)).toBeInTheDocument()
  })

  test('requires choosing an application', async () => {
    signedIn({ applications: APPS })
    const { user } = renderApp('/assistant')

    await screen.findByRole('option', { name: 'Northwind — Backend Engineer' })
    await user.click(screen.getByRole('button', { name: 'Analyse' }))

    expect(screen.getByText('Choose an application')).toBeInTheDocument()
    expect(screen.queryByRole('tablist')).not.toBeInTheDocument()
  })
})
