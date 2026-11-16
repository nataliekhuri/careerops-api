import { Link } from 'react-router'

import { Logo } from '@/components/Logo'
import { buttonClasses } from '@/components/ui/buttonStyles'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="py-6">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-6 text-slate-600">{children}</div>
    </section>
  )
}

export function Privacy() {
  return (
    <div className="min-h-screen bg-white">
      <header className="mx-auto flex max-w-3xl items-center justify-between px-4 py-5 sm:px-6">
        <Logo />
        <Link to="/" className={buttonClasses('ghost')}>
          Back to home
        </Link>
      </header>

      <main className="mx-auto max-w-3xl px-4 pb-20 sm:px-6">
        <p className="text-sm font-semibold text-brand-600">Privacy</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">How CareerOps handles your data</h1>
        <p className="mt-4 text-sm text-slate-500">
          CareerOps is a portfolio project. It is built to the same data-handling standard as a production app, but it
          is run by one person without a company, a support team, or a legal entity behind it — so treat it as a demo
          rather than a service for data you cannot afford to lose. This page explains, in plain language, what is
          stored, who can see it, and how the AI assistant works.
        </p>

        <div className="mt-2 divide-y divide-slate-100">
          <Section title="What is stored">
            <p>When you create an account, CareerOps stores:</p>
            <ul className="list-disc space-y-1 pl-5">
              <li>Your email address and name, and a password hash (never the password itself).</li>
              <li>
                The job applications, companies and interviews you add: company, role, location, notes, status and
                dates.
              </li>
              <li>
                Job descriptions you paste or save on an application, and your career profile (skills, years of
                experience, target role and CV text), if you choose to add them.
              </li>
            </ul>
            <p>
              All of this is private to your account. Every request is scoped to the signed-in user: another account's
              data is never returned, even by id — it answers exactly as if it did not exist.
            </p>
          </Section>

          <Section title="The AI career assistant">
            <p>
              The AI assistant (job match scoring, CV suggestions, interview prep) is a{' '}
              <strong>free, rule-based analyzer that runs on this server</strong>. It is not a hosted AI model: there is
              no API key, and nothing you enter — your CV text, a pasted job description, your skills — is sent to
              OpenAI, Anthropic, Google or any other third party. The analysis is a set of deterministic rules (keyword
              matching, scoring, templated question banks) over your own data, run in the same backend as the rest of
              the app.
            </p>
            <p>
              If a hosted AI provider is ever added, it will be optional, clearly labelled, and off by default — see{' '}
              <a
                href="https://github.com/nataliekhuri/careerops-api/blob/main/app/ai/providers.py"
                className="underline underline-offset-2"
                target="_blank"
                rel="noreferrer"
              >
                the provider interface in the source code
              </a>
              .
            </p>
          </Section>

          <Section title="Who can see your data">
            <p>
              Only you, through your signed-in account. The person running this project can access the production
              database directly (as any self-hosted app's operator can), but does not read, export or share individual
              users' data, and no one else has access. There are no analytics or advertising trackers in the app.
            </p>
          </Section>

          <Section title="Where your data is hosted">
            <p>
              The API and database run on Render, in Frankfurt, Germany. This project currently runs on Render's{' '}
              <strong>free</strong> plan: the free database expires 30 days after it was created and is deleted 14 days
              after that unless upgraded. If that happens, your account and data are lost. This is a known limitation of
              a free-tier demo, not a hidden retention policy — see{' '}
              <a
                href="https://github.com/nataliekhuri/careerops-api#deployment-render"
                className="underline underline-offset-2"
                target="_blank"
                rel="noreferrer"
              >
                the README
              </a>{' '}
              for details.
            </p>
          </Section>

          <Section title="Deleting your data">
            <p>
              Settings → Delete account permanently removes your account and everything linked to it (applications,
              companies, interviews, career profile) in one action, after you confirm your password. This cannot be
              undone and is not a soft delete.
            </p>
          </Section>

          <Section title="Security measures">
            <ul className="list-disc space-y-1 pl-5">
              <li>Passwords are hashed with Argon2id; CareerOps never stores or logs plain-text passwords.</li>
              <li>All traffic is encrypted with HTTPS/TLS.</li>
              <li>Sign-in is rate-limited to slow down password-guessing attempts.</li>
              <li>The source code is public and open to review.</li>
            </ul>
          </Section>

          <Section title="Contact">
            <p>
              Questions about this project or its data handling: open an issue on{' '}
              <a
                href="https://github.com/nataliekhuri/careerops-api"
                className="underline underline-offset-2"
                target="_blank"
                rel="noreferrer"
              >
                GitHub
              </a>
              .
            </p>
          </Section>
        </div>

        <p className="mt-6 text-xs text-slate-400">Last updated 14 November 2026.</p>
      </main>
    </div>
  )
}
