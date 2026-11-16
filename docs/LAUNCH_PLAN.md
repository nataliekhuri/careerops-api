# Public frontend launch plan (M6)

Goal: a public CareerOps web app on Render's free plan, talking to the existing API,
with no new costs. **Nothing in this plan has been deployed.** The configuration and
hardening below are built and tested locally, in the M6 pull request. Every step that
merges, deploys, migrates or changes a live service still needs your explicit approval.

See [FEATURES.md](FEATURES.md) for the full checklist (implemented / tested locally /
live) and [MIGRATION_AND_BACKUP_PLAN.md](MIGRATION_AND_BACKUP_PLAN.md) for the exact
migration SQL and backup steps referenced below.

## 1. Decisions needed before launch

| # | Decision | Options | Recommendation |
|---|---|---|---|
| 1 | **Database lifetime.** The free Render PostgreSQL database expires **30 days after creation** (created around 12 Nov 2026, so roughly 12 Dec 2026 — check the exact date in the Render dashboard), and is deleted 14 days after that. | a) Stay free: treat the app as a demo and recreate the database when it expires (all data lost). b) Upgrade the database to a paid plan (costs money). | For a portfolio launch, a), with the "demo, data may be reset" notice already on the [privacy page](../frontend/src/pages/Privacy.tsx). Choose b) only if real users should keep data. |
| 2 | **Public sign-up.** | Open registration, or a demo video only. | Open registration — login/registration rate limiting is built (see below). Do not publish a shared demo password: anyone could change or delete it. |
| 3 | **Production migrations** `e1ea5f0b4a8d` (#8) and `66ff5fb506ac` (#11). Both are additive and run automatically at container start. | Approve each with a backup. | Approve both, each with a backup (option A or B — see MIGRATION_AND_BACKUP_PLAN.md). |
| 4 | **Frontend URL.** | A free `onrender.com` URL, or a custom domain (costs money). | The free URL. Render assigned `careerops-web-ptuv.onrender.com` (the plain `careerops-web.onrender.com` name was already taken); `render.yaml` and `CORS_ORIGINS` are configured for the actual assigned URL. |

## 2. Merge and migration order

Each merge to `main` deploys the API automatically once CI passes. Pending migrations
run when the container starts (see "How it deploys" in MIGRATION_AND_BACKUP_PLAN.md).

1. **#6**: README links. No deploy impact.
2. **#8**: companies, interviews, dashboard. **Back up first.** Migration `e1ea5f0b4a8d`.
3. **#9, #10**: frontend code only. The Docker image excludes `frontend/`, so the API does not change.
4. **#11**: AI assistant. **Back up again.** Migration `66ff5fb506ac`.
5. **M6 PR** (this one): rate limiting, security headers, privacy page, the static-site Blueprint entry, `CORS_ORIGINS`, and this documentation. No migration.
6. **Sync the Blueprint in the Render Dashboard** (a separate, manual step — Render does not create the static site just because `render.yaml` changed in Git): this is what actually creates `careerops-web` and makes the frontend live.

Rollback: revert the merge commit on `main`, which redeploys the previous image/site.
Each migration has a tested downgrade, but the safest database rollback is restoring
the backup taken just before.

## 3. What is in the M6 pull request

### 3.1 Backend hardening — done, tested

- **Login rate limiting**: 5 attempts per email + 20 per IP, both per 15 minutes, on `/auth/login`; 5 registrations per IP per hour on `/auth/register`. 429 with `Retry-After`. `app/core/rate_limit.py`, `app/api/rate_limit.py`, `tests/test_rate_limit.py` (12 tests).
- **Security response headers** on every API response: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, and `Strict-Transport-Security` once a request has reached the API over HTTPS. `app/core/security_headers.py`, `tests/test_security_headers.py` (4 tests).
- Request size limits were already in place (job descriptions 20,000 characters, CVs 30,000).
- Full write-up: [SECURITY_REVIEW.md](SECURITY_REVIEW.md).

### 3.2 Static site and CORS — live

`render.yaml` has a second service, `careerops-web` (free static site, builds
`frontend/`), with a CSP, caching and security headers. Render assigned it
`careerops-web-ptuv.onrender.com` (the plain `careerops-web.onrender.com` name was
already taken when the Blueprint was synced), so `CORS_ORIGINS` on the API is set to
that actual assigned URL. Sanity-checked by tests in `tests/test_deploy_config.py`
(static sites have no `plan`/`region` field, builds from `frontend/`, is a single-page
app rewrite, points at the live API, has every security header, long cache only on
hashed assets).

### 3.3 Privacy notice page — done, tested

`/privacy`, public, linked from the landing page footer and from the registration form.
Explains what is stored, that the AI assistant is the free built-in analyzer (nothing
sent to a third party), who can see the data, where it is hosted, the free-database
expiry caveat, how to delete an account, and the security measures in place. 3 tests in
`frontend/src/pages/public-pages.test.tsx`.

### 3.4 Production smoke test — done, dry-run verified locally

`scripts/smoke_test.py` (stdlib only, no extra install): registers a throwaway account,
exercises every main flow (companies, applications, board move, interviews, dashboard,
all 4 AI assistant endpoints, skill insights), checks security headers, confirms
isolation (a non-existent id answers 404, not a crash), deletes the account, and
confirms it is really gone. Exits non-zero on any failure.

```bash
python scripts/smoke_test.py --api-url https://careerops-api.onrender.com
python scripts/smoke_test.py --api-url https://careerops-api.onrender.com \
    --web-url https://careerops-web-ptuv.onrender.com
```

Dry-run verified against a local instance on a throwaway database schema (24 checks,
all passing); **not yet run against the live Render API** — that is itself a write
action against production and needs the same go-ahead as any other production step.

### 3.5 Not done in M6 (left for later, listed here so it isn't lost)

- A "starting the server, this can take up to a minute" message while the free API
  wakes from sleep, instead of a bare spinner.
- Open Graph tags / a social preview image for link previews (LinkedIn, etc.).
- A hosted AI provider (needs approval — costs money, sends data to a third party).
- Email verification and password reset by email (needs an email provider).
- A CAPTCHA on registration (needs a third-party key and would need approval); the
  current per-IP rate limit slows but does not stop a distributed script.

## 4. Go-live checklist

- [x] Decisions 1–4 made
- [x] Backup taken, then #8 merged; production migration `e1ea5f0b4a8d` approved and succeeded
- [x] #9, #10 merged
- [x] Backup taken, then #11 merged; production migration `66ff5fb506ac` approved and succeeded
- [x] M6 PR merged
- [x] Blueprint synced in the Render Dashboard — `careerops-web` was created. Render assigned
      it **`careerops-web-ptuv.onrender.com`** (the plain `careerops-web.onrender.com` name
      was already taken), so `CORS_ORIGINS` was updated to match after sync.
- [x] Manual click-through of every major flow against production (register, login,
      logout, account isolation, applications/companies/interviews CRUD, board, dashboard,
      all 4 AI assistant tabs, mobile layout) — see the launch verification report.
      `scripts/smoke_test.py` was written and dry-run verified locally but not run against
      production in this pass (the manual walkthrough covered the same flows).
- [x] Response headers spot-checked in a real browser (CSP, nosniff, HSTS) — confirmed on
      both the API and the static site.
- [ ] Database expiry date noted in the calendar (if staying on the free plan)
- [x] README updated with the live frontend URL
- [ ] LinkedIn post published — see [LINKEDIN_LAUNCH.md](LINKEDIN_LAUNCH.md)

## 5. After launch

- Watch the Render logs for 5xx errors and slow requests during the first days.
- Check the free instance hours (750/month) and static-site bandwidth in the Render dashboard.
- Optional free uptime check on `/health` (keep the interval reasonable; it also keeps the instance awake and uses hours).
