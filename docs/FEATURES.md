# CareerOps feature checklist

Status as of 13 November 2026.

- **Live** = merged to `main` and deployed to Render.
- **Ready** = built, tested and green in CI, waiting in an open pull request for review.
- **Planned** = not built yet.

Pull requests are stacked: #8 → #9 → #10 → M5. Each one only shows its own changes.

## Summary

| Milestone | Scope | PR | Database migration | Status |
|---|---|---|---|---|
| M1 | Auth, per-user data, applications API, Docker, CI, Render | #1–#5, #7 | `41cc45136ccd`, `9c42a113f669` (applied) | **Live** (API 2.0.0) |
| — | README live-demo links | #6 | none | Ready |
| M2 | Companies, interviews, dashboard statistics API | #8 | `e1ea5f0b4a8d` (approval needed) | Ready |
| M3 | React frontend: auth, applications, companies | #9 | none | Ready |
| M4 | Dashboard charts, Kanban board, interview calendar, settings | #10 | none | Ready |
| M5 | AI career assistant | M5 PR | `66ff5fb506ac` (approval needed) | Ready |
| M6 | Public frontend launch | — | none | Planned ([launch plan](LAUNCH_PLAN.md)) |

## Backend API

- [x] Register, log in (JWT, Argon2id password hashing), profile, password change, account deletion (**Live**)
- [x] Applications: CRUD, `PATCH`, status workflow enforced in the API and the database (**Live**)
- [x] Filtering, sorting, pagination with `X-Total-Count` (**Live**)
- [x] Per-user isolation: other users' records answer 404, references to them answer 422 (**Live**)
- [x] Liveness and readiness health checks, safe error responses, database timeout (**Live**)
- [x] Companies linked to applications (**Ready**, #8)
- [x] Interviews with calendar ranges and outcomes; database-enforced same owner as the application (**Ready**, #8)
- [x] Dashboard statistics: totals, rates, 12-week activity, top companies, upcoming interviews (**Ready**, #8)
- [x] Job descriptions on applications (**Ready**, M5)
- [x] Career profile: skills, experience, target role, CV text (**Ready**, M5)
- [ ] Login rate limiting / brute-force protection (**Planned**: recommended before a public launch)
- [ ] Email verification and password reset by email (**Planned**: needs an email provider)

## AI career assistant (M5)

- [x] Job description analysis: skills with required vs. nice-to-have, evidence line, seniority, years, work mode, role family
- [x] Skill extraction that keeps look-alikes apart (Java/JavaScript, SQL/NoSQL, C/C++/C#, Go vs. "go")
- [x] Explainable match score: weighted components, matched / related / missing skills with reasons, next steps
- [x] CV review: structure, length, measurable results, action verbs, weak phrases, links, job keywords; prioritised suggestions with examples
- [x] Role-specific interview prep: technical questions with tips, questions about your gaps, STAR behavioural questions, questions to ask, company research, upcoming interviews
- [x] Skill demand across your applications, with coverage and what to learn next
- [x] Uses real data: the user's applications, job descriptions, companies, interviews and career profile
- [x] Provider interface for future AI services; only the free built-in provider can be configured
- [ ] Hosted LLM provider (**Planned**, needs approval: costs money and sends data to a third party)

## Frontend

- [x] Landing page, register and sign in, session expiry handling (**Ready**, #9)
- [x] Applications: table, search, filters, sorting, pagination, create / edit / delete, detail page (**Ready**, #9)
- [x] Companies: list, detail with linked applications, create / edit / delete (**Ready**, #9)
- [x] Dashboard: key figures, weekly chart with text alternative, pipeline, upcoming interviews, top companies (**Ready**, #10)
- [x] Kanban board: drag with mouse, touch or keyboard, or "Move to"; optimistic update with rollback (**Ready**, #10)
- [x] Interview calendar: month grid, day list, schedule / edit / outcome / delete, time-zone safe (**Ready**, #10)
- [x] Settings: profile, password, account deletion (**Ready**, #10)
- [x] AI assistant page and career profile in Settings; job description on applications (**Ready**, M5)
- [x] Responsive layouts (checked at 390 px and 1440 px), loading, empty and error states
- [x] Accessibility: labelled forms, keyboard support (board, tabs, dialogs), skip link, chart text alternatives
- [ ] Public deployment as a Render static site (**Planned**, M6)
- [ ] Notice while the free API wakes up (about a minute after 15 minutes idle) (**Planned**, M6)
- [ ] Privacy notice page (CVs are personal data) (**Planned**, M6)

## Quality

| Check | Result |
|---|---|
| Backend tests (pytest, real PostgreSQL in throwaway schemas) | 329 passing |
| Frontend tests (Vitest, Testing Library, MSW) | 64 passing |
| Migration tests: upgrade, downgrade, existing data kept | Every migration |
| OpenAPI contract: generated frontend types must match the backend | Enforced in CI |
| Lint and format: Ruff, oxlint, Prettier; TypeScript strict | Enforced in CI |
| Docker image build and Compose smoke test | Enforced in CI |
| Real-browser runs (headless Edge against the real API) | Board drag and drop, AI assistant, mobile layouts, no console errors |
