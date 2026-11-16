# CareerOps feature checklist

Status as of 16 November 2026.

- **Live** = merged to `main`, deployed to Render, confirmed working on the real URL.
- **Verified in production** = Live, and specifically exercised end to end against the
  real deployment (not just a local test) during launch verification.
- **Planned** = not built.

Pull requests are stacked: #8 → #9 → #10 → #11 → #12 (M6). All five are merged to `main`
and deployed.

## Summary

| Milestone | Scope | PR | Database migration | Status |
|---|---|---|---|---|
| M1 | Auth, per-user data, applications API, Docker, CI, Render | #1–#5, #7 | `41cc45136ccd`, `9c42a113f669` (applied) | **Live** (API 2.0.0) |
| — | README live-demo links | #6 | none | **Live** |
| M2 | Companies, interviews, dashboard statistics API | #8 | `e1ea5f0b4a8d` (applied, verified) | **Live** |
| M3 | React frontend: auth, applications, companies | #9 | none | **Live** |
| M4 | Dashboard charts, Kanban board, interview calendar, settings | #10 | none | **Live** |
| M5 | AI career assistant | #11 | `66ff5fb506ac` (applied, verified) | **Live** |
| M6 | Rate limiting, security headers, privacy page, static-site deployment, CORS | #12 | none | **Live** |

**Everything is live**, at API version 2.3.0:
[careerops-api.onrender.com](https://careerops-api.onrender.com) and
[careerops-web-ptuv.onrender.com](https://careerops-web-ptuv.onrender.com). See
[MIGRATION_AND_BACKUP_PLAN.md](MIGRATION_AND_BACKUP_PLAN.md) and
[LAUNCH_PLAN.md](LAUNCH_PLAN.md) for how it got there.

## Backend API

- [x] Register, log in (JWT, Argon2id password hashing), profile, password change, account deletion — **Verified in production**
- [x] Applications: CRUD, `PATCH`, status workflow enforced in the API and the database — **Verified in production**
- [x] Filtering, sorting, pagination with `X-Total-Count` — **Live**
- [x] Per-user isolation: other users' records answer 404, references to them answer 422 — **Verified in production** (a second test account could not see or reach the first account's application, company or any other data by id)
- [x] Liveness and readiness health checks, safe error responses, database timeout — **Verified in production**
- [x] Companies linked to applications — **Verified in production**
- [x] Interviews with calendar ranges and outcomes; database-enforced same owner as the application — **Verified in production**
- [x] Dashboard statistics: totals, rates, 12-week activity, top companies, upcoming interviews — **Verified in production**
- [x] Job descriptions on applications — **Verified in production**
- [x] Career profile: skills, experience, target role, CV text — **Verified in production**
- [x] **Login/registration rate limiting**: 5/email + 20/IP per 15 min on login, 5/IP per hour on registration, 429 + `Retry-After` — **Verified in production** (confirmed the 6th rapid login attempt returns 429 with a `Retry-After` header)
- [x] **Security response headers** (nosniff, frame-options, referrer-policy, permissions-policy, conditional HSTS) — **Verified in production**
- [ ] Email verification and password reset by email — Planned (needs an email provider)
- [ ] CAPTCHA on registration — Planned (needs a third-party key and approval; the per-IP rate limit above is a partial mitigation)

## AI career assistant (M5)

All items below: **Verified in production** — analysed a real saved job description end
to end through the live frontend.

- [x] Job description analysis: skills with required vs. nice-to-have, evidence line, seniority, years, work mode, role family
- [x] Skill extraction that keeps look-alikes apart (Java/JavaScript, SQL/NoSQL, C/C++/C#, Go vs. "go")
- [x] Explainable match score: weighted components, matched / related / missing skills with reasons, next steps
- [x] CV review: structure, length, measurable results, action verbs, weak phrases, links, job keywords; prioritised suggestions with examples
- [x] Role-specific interview prep: technical questions with tips, questions about your gaps, STAR behavioural questions, questions to ask, company research, upcoming interviews
- [x] Skill demand across your applications, with coverage and what to learn next
- [x] Uses real data: the user's applications, job descriptions, companies, interviews and career profile
- [x] Provider interface for future AI services; only the free built-in provider can be configured
- [ ] Hosted LLM provider — Planned, needs approval (costs money and sends data to a third party)

## Frontend

All items below: **Verified in production** at
[careerops-web-ptuv.onrender.com](https://careerops-web-ptuv.onrender.com).

- [x] Landing page, register and sign in, session expiry handling
- [x] Applications: table, search, filters, sorting, pagination, create / edit / delete, detail page
- [x] Companies: list, detail with linked applications, create / edit / delete
- [x] Dashboard: key figures, weekly chart with text alternative, pipeline, upcoming interviews, top companies
- [x] Kanban board: drag with mouse, touch or keyboard, or "Move to"; optimistic update with rollback (verified the "Move to" path)
- [x] Interview calendar: month grid, day list, schedule / edit / outcome / delete, time-zone safe
- [x] Settings: profile, password, career profile, account deletion
- [x] AI assistant page and career profile in Settings; job description on applications
- [x] **Privacy notice page** (`/privacy`), linked from the landing footer and registration
- [x] Responsive layouts (checked at mobile width in production), loading, empty and error states
- [x] Accessibility: labelled forms, keyboard support (board, tabs, dialogs), skip link, chart text alternatives
- [x] Public deployment as a Render static site — **Live** at `careerops-web-ptuv.onrender.com` (Render assigned a suffixed name; the plain `careerops-web.onrender.com` was already taken)
- [ ] Notice while the free API wakes up (about a minute after 15 minutes idle) — Planned
- [ ] Open Graph tags / social preview image for link sharing — Planned

## Production readiness (M6)

- [x] `CORS_ORIGINS` set to the real frontend origin in `render.yaml` — **Verified in production** (preflight and simple requests from `careerops-web-ptuv.onrender.com` are allowed; other origins are not)
- [x] Security review covering auth, headers, error handling and config — Written up, [SECURITY_REVIEW.md](SECURITY_REVIEW.md)
- [x] Database migration and backup plan for #8 and #11 — Executed: both migrations applied to production, each preceded by a verified `pg_dump` backup
- [x] Production smoke-test script (`scripts/smoke_test.py`) — Tested locally (24 checks, dry run against a local throwaway database); the equivalent flows were verified manually against production instead of running the script live
- [x] LinkedIn launch package (post copy, screenshot picks, demo video script) — [LINKEDIN_LAUNCH.md](LINKEDIN_LAUNCH.md), ready to post now that the link is live

## Quality

| Check | Result |
|---|---|
| Backend tests (pytest, real PostgreSQL in throwaway schemas) | 352 passing |
| Frontend tests (Vitest, Testing Library, MSW) | 67 passing |
| Migration tests: upgrade, downgrade, existing data kept | Every migration |
| OpenAPI contract: generated frontend types must match the backend | Enforced in CI |
| Lint and format: Ruff, oxlint, Prettier; TypeScript strict | Enforced in CI |
| Docker image build and Compose smoke test | Enforced in CI |
| Deployment config checks (`render.yaml` sanity) | 17 tests, `tests/test_deploy_config.py` |
| Real-browser runs (headless Edge against the real API) | Board drag and drop, AI assistant, mobile layouts, no console errors |
| Manual production verification | Registration, login, logout, two-account isolation, applications/companies/interviews CRUD, board, dashboard, all 4 AI assistant tabs, mobile layout, security headers, rate limiting, privacy page — all passed against the live deployment |
| Production smoke test (`scripts/smoke_test.py`) | Written and dry-run verified locally; not run against production in this pass |
