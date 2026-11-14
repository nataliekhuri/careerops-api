# CareerOps feature checklist

Status as of 14 November 2026.

- **Live** = merged to `main`, deployed to Render, confirmed working on the real URL.
- **Tested locally** = code complete, covered by automated tests that pass, and often
  also verified in a real browser against a local throwaway database. Waiting in an
  open pull request; **not deployed**.
- **Configured, not applied** = infrastructure/config (e.g. a `render.yaml` service)
  that exists in the repository and is checked by tests, but has not been created on
  Render yet — that is a separate, manual step (syncing the Blueprint).
- **Planned** = not built.

Pull requests are stacked: #8 → #9 → #10 → #11 → #12 (M6). Each shows only its own
changes.

## Summary

| Milestone | Scope | PR | Database migration | Status |
|---|---|---|---|---|
| M1 | Auth, per-user data, applications API, Docker, CI, Render | #1–#5, #7 | `41cc45136ccd`, `9c42a113f669` (applied) | **Live** (API 2.0.0) |
| — | README live-demo links | #6 | none | Tested locally |
| M2 | Companies, interviews, dashboard statistics API | #8 | `e1ea5f0b4a8d` (approval needed) | Tested locally |
| M3 | React frontend: auth, applications, companies | #9 | none | Tested locally |
| M4 | Dashboard charts, Kanban board, interview calendar, settings | #10 | none | Tested locally |
| M5 | AI career assistant | #11 | `66ff5fb506ac` (approval needed) | Tested locally |
| M6 | Rate limiting, security headers, privacy page, static-site config, smoke test | #12 | none | Tested locally |

**Nothing past API 2.0.0 is live.** M2–M6 are all built, tested and waiting for
approval, in that order — see [MIGRATION_AND_BACKUP_PLAN.md](MIGRATION_AND_BACKUP_PLAN.md)
and [LAUNCH_PLAN.md](LAUNCH_PLAN.md).

## Backend API

- [x] Register, log in (JWT, Argon2id password hashing), profile, password change, account deletion — **Live**
- [x] Applications: CRUD, `PATCH`, status workflow enforced in the API and the database — **Live**
- [x] Filtering, sorting, pagination with `X-Total-Count` — **Live**
- [x] Per-user isolation: other users' records answer 404, references to them answer 422 — **Live**
- [x] Liveness and readiness health checks, safe error responses, database timeout — **Live**
- [x] Companies linked to applications — Tested locally, #8
- [x] Interviews with calendar ranges and outcomes; database-enforced same owner as the application — Tested locally, #8
- [x] Dashboard statistics: totals, rates, 12-week activity, top companies, upcoming interviews — Tested locally, #8
- [x] Job descriptions on applications — Tested locally, #11
- [x] Career profile: skills, experience, target role, CV text — Tested locally, #11
- [x] **Login/registration rate limiting**: 5/email + 20/IP per 15 min on login, 5/IP per hour on registration, 429 + `Retry-After` — Tested locally, #12 (12 tests)
- [x] **Security response headers** (nosniff, frame-options, referrer-policy, permissions-policy, conditional HSTS) — Tested locally, #12 (4 tests)
- [ ] Email verification and password reset by email — Planned (needs an email provider)
- [ ] CAPTCHA on registration — Planned (needs a third-party key and approval; the per-IP rate limit above is a partial mitigation)

## AI career assistant (M5)

All items below: Tested locally, #11.

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

- [x] Landing page, register and sign in, session expiry handling — Tested locally, #9
- [x] Applications: table, search, filters, sorting, pagination, create / edit / delete, detail page — Tested locally, #9
- [x] Companies: list, detail with linked applications, create / edit / delete — Tested locally, #9
- [x] Dashboard: key figures, weekly chart with text alternative, pipeline, upcoming interviews, top companies — Tested locally, #10
- [x] Kanban board: drag with mouse, touch or keyboard, or "Move to"; optimistic update with rollback — Tested locally, #10
- [x] Interview calendar: month grid, day list, schedule / edit / outcome / delete, time-zone safe — Tested locally, #10
- [x] Settings: profile, password, account deletion — Tested locally, #10
- [x] AI assistant page and career profile in Settings; job description on applications — Tested locally, #11
- [x] **Privacy notice page** (`/privacy`), linked from the landing footer and registration — Tested locally, #12 (3 tests)
- [x] Responsive layouts (checked at 390 px and 1440 px), loading, empty and error states
- [x] Accessibility: labelled forms, keyboard support (board, tabs, dialogs), skip link, chart text alternatives
- [ ] Public deployment as a Render static site — **Configured, not applied** (`render.yaml`, service `careerops-web`; syncing the Blueprint in the Render Dashboard is the remaining step)
- [ ] Notice while the free API wakes up (about a minute after 15 minutes idle) — Planned
- [ ] Open Graph tags / social preview image for link sharing — Planned

## Production readiness (M6)

- [x] `CORS_ORIGINS` set to the real frontend origin in `render.yaml` — **Configured, not applied** (takes effect once #12 is merged and deployed)
- [x] Security review covering auth, headers, error handling and config — Written up, [SECURITY_REVIEW.md](SECURITY_REVIEW.md)
- [x] Database migration and backup plan for #8 and #11 — Written up, [MIGRATION_AND_BACKUP_PLAN.md](MIGRATION_AND_BACKUP_PLAN.md)
- [x] Production smoke-test script (`scripts/smoke_test.py`) — Tested locally (24 checks, dry run against a local throwaway database); **not yet run against the live API**
- [x] LinkedIn launch package (post copy, screenshot picks, demo video script) — [LINKEDIN_LAUNCH.md](LINKEDIN_LAUNCH.md)

## Quality

| Check | Result |
|---|---|
| Backend tests (pytest, real PostgreSQL in throwaway schemas) | 352 passing |
| Frontend tests (Vitest, Testing Library, MSW) | 67 passing |
| Migration tests: upgrade, downgrade, existing data kept | Every migration |
| OpenAPI contract: generated frontend types must match the backend | Enforced in CI |
| Lint and format: Ruff, oxlint, Prettier; TypeScript strict | Enforced in CI |
| Docker image build and Compose smoke test | Enforced in CI |
| Deployment config checks (`render.yaml` sanity) | 18 tests, `tests/test_deploy_config.py` |
| Real-browser runs (headless Edge against the real API) | Board drag and drop, AI assistant, mobile layouts, no console errors |
| Production smoke test | Written and dry-run verified locally; not yet run against production |
