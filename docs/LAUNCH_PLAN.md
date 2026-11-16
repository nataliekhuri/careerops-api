# Public frontend launch plan (M6)

Goal: a public CareerOps web app on Render's free plan, talking to the existing API,
with no new costs. **Nothing in this plan has been done yet.** Every step that merges,
deploys, migrates or changes a live service needs explicit approval first.

## 1. Decisions needed before launch

| # | Decision | Options | Recommendation |
|---|---|---|---|
| 1 | **Database lifetime.** The free Render PostgreSQL database expires **30 days after creation** (ours was created around 12 Nov 2026, so roughly 12 Dec 2026; check the Render dashboard), and is deleted 14 days later. | a) Stay free: treat the app as a demo and recreate the database when it expires (all data lost). b) Upgrade the database to a paid plan (costs money). | For a portfolio launch, a), with a clear "demo, data may be reset" notice. Choose b) only if real users should keep data. |
| 2 | **Public sign-up.** | Open registration, or a demo video only. | Open registration, plus login rate limiting (step 3.1). Do not publish a shared demo password: anyone could change or delete it. |
| 3 | **Production migrations** `e1ea5f0b4a8d` (#8) and `66ff5fb506ac` (#11). Both are additive and run automatically at container start. | Approve each with a backup. | Approve both, each with backup option A or B from the PR #8 plan. |
| 4 | **Frontend URL.** | `careerops-web.onrender.com` (free), or a custom domain (domain costs money). | The free `onrender.com` URL. |

## 2. Merge and migration order

Each merge to `main` deploys the API automatically once CI passes. Pending migrations
run when the container starts.

1. **#6**: README links. No deploy impact.
2. **#8**: companies, interviews, dashboard. Back up the database first (see the PR #8 comment). Migration `e1ea5f0b4a8d`. Smoke test: `/health/ready`, register, `GET /dashboard/stats`.
3. **#9, #10**: frontend code only. The Docker image excludes `frontend/`, so the API does not change.
4. **#11**: AI assistant. Back up again, then migration `66ff5fb506ac` (exact SQL in the PR). Smoke test: `GET /ai/provider`, `PUT /users/me/career-profile`, `POST /ai/match`.
5. **M6 PR** (this plan): static site, CORS and launch hardening.

Rollback: revert the merge commit on `main`, which redeploys the previous image. Each
migration has a tested downgrade, but the safest database rollback is restoring the
backup taken just before.

## 3. Work to do in the M6 pull request

### 3.1 Hardening (backend)

- **Login rate limiting:** for example 5 failed attempts per email per 15 minutes, plus a per-IP limit on `/auth/register` and `/auth/login`. An in-memory limiter is enough on a single free instance. Answer 429 with `Retry-After`.
- Upper bounds for request bodies are already set (job descriptions 20,000 characters, CV 30,000).
- Keep `CORS_ORIGINS` to the exact frontend origin, no wildcards.

### 3.2 Static site (Render Blueprint)

Add to `render.yaml`. This is not applied yet: syncing the Blueprint creates the service.

```yaml
  - type: web
    name: careerops-web
    runtime: static
    rootDir: frontend
    buildCommand: npm ci && npm run build
    staticPublishPath: dist
    branch: main
    autoDeployTrigger: checksPass
    pullRequestPreviewsEnabled: false
    envVars:
      - key: VITE_API_URL
        value: https://careerops-api.onrender.com
    routes:
      - type: rewrite        # single-page app: every route serves index.html
        source: /*
        destination: /index.html
    headers:
      - path: /assets/*
        name: Cache-Control
        value: public, max-age=31536000, immutable
      - path: /*
        name: Content-Security-Policy
        value: "default-src 'self'; connect-src 'self' https://careerops-api.onrender.com; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
      - path: /*
        name: X-Content-Type-Options
        value: nosniff
      - path: /*
        name: Referrer-Policy
        value: strict-origin-when-cross-origin
```

On the API service, add `CORS_ORIGINS=https://careerops-web.onrender.com`.

Render static sites are free, include a CDN and TLS, and have a monthly bandwidth
allowance that is ample for a portfolio project.

### 3.3 Frontend polish

- When the API takes more than about 3 seconds to answer (free instance waking up), show "Starting the server, this can take up to a minute…" instead of a bare spinner.
- Add a privacy notice page: what is stored (account, applications, CV text), that the AI analysis runs on the server with no third parties, how to delete the account (Settings → Delete account), and the "demo, data may be reset" notice if decision 1a is chosen.
- Add a page title and description per route, Open Graph tags and a social preview image (the dashboard screenshot) for LinkedIn link previews.

### 3.4 Checks in CI and before go-live

- Production build runs against `VITE_API_URL` set to the real API.
- A real-browser smoke test against the deployed site: register → add an application with a job description → board move → schedule an interview → AI match → delete the account.
- Lighthouse: accessibility and best practices at 90 or higher on the landing and dashboard pages.
- No console errors; CSP has no violations.

## 4. Go-live checklist

- [ ] Decisions 1–4 made
- [ ] Backups taken and verified, then #8 merged; production migration `e1ea5f0b4a8d` succeeded
- [ ] #9, #10 merged
- [ ] Backup taken, then #11 merged; production migration `66ff5fb506ac` succeeded
- [ ] M6 PR merged; static site live; `CORS_ORIGINS` set
- [ ] Smoke test on production passed (section 3.4)
- [ ] Response headers checked (CSP, nosniff, caching)
- [ ] Database expiry date noted in the calendar (if staying on the free plan)
- [ ] README updated with the live frontend URL
- [ ] LinkedIn post: screenshots from `docs/screenshots/`, a short screen recording, and links to the live app and the repository

## 5. After launch

- Watch the Render logs for 5xx errors and slow requests during the first days.
- Check the free instance hours (750 per month) and bandwidth in the Render dashboard.
- Optional free uptime check on `/health` (keep the interval reasonable; it also keeps the instance awake and uses hours).
