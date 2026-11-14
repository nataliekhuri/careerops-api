# Database migration and backup plan

Consolidates the two pending production migrations (PR #8, PR #11) into one reference.
**Neither has been run against the live database.** Each needs your explicit approval,
taken in order, with a backup first.

Live database: Render `careerops-db` (PostgreSQL 18, Frankfurt). Live API: **2.0.0**,
currently at revision `9c42a113f669`. Local development database: also at
`9c42a113f669` (one migration ahead of the last approved production state — approved
locally, not yet approved for production; see "Current state" below).

## Current state

| | Local dev DB | Production (Render `careerops-db`) |
|---|---|---|
| Revision | `9c42a113f669` | `9c42a113f669` |
| API version | n/a (run from source) | **2.0.0** |

Both are one migration behind PR #8 (`e1ea5f0b4a8d`) and two behind PR #11
(`66ff5fb506ac`). Local and production are migrated **separately and never
automatically**: approving a migration here only prepares it, it does not run it
anywhere until you say so.

## Order

Migrations must be applied in order, each as its own approved step:

```
9c42a113f669  (current — both local and production)
      │
      ▼  PR #8 — companies, interviews, dashboard
e1ea5f0b4a8d
      │
      ▼  PR #11 — career profiles, job descriptions (AI assistant)
66ff5fb506ac  (current head)
```

You can approve PR #8's migration without approving PR #11's — they are independent
steps. PR #11's migration cannot be applied before PR #8's (Alembic enforces the chain).

## Backup options

The Render database has `ipAllowList: []` (no access from the internet) and the free
plan has no automatic backups. Before either production migration, choose one:

- **Option A — take a `pg_dump`** (recommended once any real account exists):
  1. In the Render Dashboard, temporarily add your current IP to `careerops-db`'s
     "Access Control" list.
  2. Copy the **External Database URL** from the Render Dashboard. Store it only in a
     local, gitignored `.env`-style file (e.g. as `RENDER_DATABASE_URL`) — never paste
     it into chat, a commit, or a script argument that ends up in shell history.
  3. Dump with a matching **PostgreSQL 18** client:
     ```bash
     pg_dump "$RENDER_DATABASE_URL" --format=custom --file=careerops-backup-$(date +%Y%m%d-%H%M).dump
     ```
  4. Verify the dump is readable without restoring it:
     ```bash
     pg_restore --list careerops-backup-*.dump | head
     ```
  5. Remove your IP from the Access Control list again.
  6. Keep the `.dump` file somewhere private, outside the repository (it contains real
     user data: emails, password hashes, applications).

- **Option B — proceed without a dump**: acceptable only while the database holds no
  real accounts (demo/test data only), since both migrations below are additive and
  change no existing row.

## PR #8 — `9c42a113f669 → e1ea5f0b4a8d` (companies, interviews, dashboard)

Additive only: one new column (`applications.company_id`, nullable) and two new empty
tables (`companies`, `interviews`). No existing column is changed or removed, no
existing row is modified.

<details><summary>Exact upgrade SQL</summary>

```sql
BEGIN;
-- Running upgrade 9c42a113f669 -> e1ea5f0b4a8d
CREATE TABLE companies (
    id SERIAL NOT NULL,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    website VARCHAR(500) DEFAULT '' NOT NULL,
    industry VARCHAR(100) DEFAULT '' NOT NULL,
    location VARCHAR(255) DEFAULT '' NOT NULL,
    notes TEXT DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT companies_pkey PRIMARY KEY (id),
    CONSTRAINT fk_companies_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_companies_user_id UNIQUE (user_id, name)
);
CREATE INDEX ix_companies_user_id ON companies (user_id);
ALTER TABLE applications ADD CONSTRAINT uq_applications_id UNIQUE (id, user_id);
ALTER TABLE applications ADD COLUMN company_id INTEGER;
CREATE INDEX ix_applications_company_id ON applications (company_id);
ALTER TABLE applications ADD CONSTRAINT fk_applications_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE SET NULL;
CREATE TABLE interviews (
    id SERIAL NOT NULL,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT '60' NOT NULL,
    interview_type VARCHAR(20) DEFAULT 'video' NOT NULL,
    location VARCHAR(500) DEFAULT '' NOT NULL,
    interviewer VARCHAR(255) DEFAULT '' NOT NULL,
    notes TEXT DEFAULT '' NOT NULL,
    outcome VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT interviews_pkey PRIMARY KEY (id),
    CONSTRAINT ck_interviews_interview_type CHECK (interview_type IN ('phone', 'video', 'onsite', 'technical', 'behavioral', 'other')),
    CONSTRAINT ck_interviews_outcome CHECK (outcome IN ('pending', 'passed', 'failed', 'cancelled')),
    CONSTRAINT ck_interviews_duration_minutes CHECK (duration_minutes BETWEEN 1 AND 600),
    CONSTRAINT fk_interviews_application_id_applications FOREIGN KEY(application_id, user_id) REFERENCES applications (id, user_id) ON DELETE CASCADE,
    CONSTRAINT fk_interviews_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_interviews_application_id ON interviews (application_id);
CREATE INDEX ix_interviews_user_id_scheduled_at ON interviews (user_id, scheduled_at);
UPDATE alembic_version SET version_num='e1ea5f0b4a8d' WHERE alembic_version.version_num = '9c42a113f669';
COMMIT;
```
</details>

<details><summary>Exact rollback SQL</summary>

```sql
BEGIN;
-- Running downgrade e1ea5f0b4a8d -> 9c42a113f669
DROP INDEX ix_interviews_user_id_scheduled_at;
DROP INDEX ix_interviews_application_id;
DROP TABLE interviews;
ALTER TABLE applications DROP CONSTRAINT fk_applications_company_id_companies;
DROP INDEX ix_applications_company_id;
ALTER TABLE applications DROP COLUMN company_id;
ALTER TABLE applications DROP CONSTRAINT uq_applications_id;
DROP INDEX ix_companies_user_id;
DROP TABLE companies;
UPDATE alembic_version SET version_num='9c42a113f669' WHERE alembic_version.version_num = 'e1ea5f0b4a8d';
COMMIT;
```
</details>

**Effect on existing data:** `users` untouched; every existing `applications` row keeps
all its values and gets `company_id = NULL`; `companies` and `interviews` start empty.

**Verification after deploy:** `/openapi.json` reports `2.1.0` and lists `/companies`,
`/interviews`, `/dashboard/stats`; `/health/ready` is `ready`; with two throwaway
accounts, create a company → link an application → schedule an interview → check
dashboard totals, then confirm the second account sees none of it (404 / 422 "not
found"). The full flow is also covered by `scripts/smoke_test.py`.

## PR #11 — `e1ea5f0b4a8d → 66ff5fb506ac` (career profiles, job descriptions)

Additive only: one new column (`applications.job_description`, `NOT NULL DEFAULT ''`)
and one new empty table (`career_profiles`). PostgreSQL 11+ adds a column with a
constant default without rewriting the table, so this is fast even on a non-empty
`applications` table.

<details><summary>Exact upgrade SQL</summary>

```sql
BEGIN;

-- Running upgrade e1ea5f0b4a8d -> 66ff5fb506ac

ALTER TABLE applications ADD COLUMN job_description TEXT DEFAULT '' NOT NULL;

CREATE TABLE career_profiles (
    user_id INTEGER NOT NULL,
    headline VARCHAR(255) DEFAULT '' NOT NULL,
    target_role VARCHAR(255) DEFAULT '' NOT NULL,
    years_experience INTEGER,
    skills JSONB DEFAULT '[]'::jsonb NOT NULL,
    cv_text TEXT DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT career_profiles_pkey PRIMARY KEY (user_id),
    CONSTRAINT ck_career_profiles_years_experience CHECK (years_experience BETWEEN 0 AND 60),
    CONSTRAINT fk_career_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='66ff5fb506ac' WHERE alembic_version.version_num = 'e1ea5f0b4a8d';

COMMIT;
```
</details>

<details><summary>Exact rollback SQL</summary>

```sql
BEGIN;

-- Running downgrade 66ff5fb506ac -> e1ea5f0b4a8d

DROP TABLE career_profiles;

ALTER TABLE applications DROP COLUMN job_description;

UPDATE alembic_version SET version_num='e1ea5f0b4a8d' WHERE alembic_version.version_num = '66ff5fb506ac';

COMMIT;
```
</details>

**Effect on existing data:** every existing `applications` row keeps all its values and
gets `job_description = ''`; `career_profiles` starts empty. Rollback drops
`career_profiles` and the job descriptions (that data is lost); applications and their
other fields are kept.

**Verification after deploy:** `/openapi.json` reports `2.3.0`+ and lists
`/users/me/career-profile`, `/ai/*`; `GET /ai/provider` returns the free `builtin`
provider; with a throwaway account, save a career profile and run a match against a
saved application, then confirm a second account cannot reach the first account's
application via the AI endpoints (422 "not found"). The full flow is also covered by
`scripts/smoke_test.py`.

## How either migration deploys (same mechanism for both)

1. Merge the PR → CI runs on `main` (lint, test, docker).
2. Render auto-deploys **only** after checks pass (`autoDeployTrigger: checksPass`).
3. The new container runs `alembic upgrade head` on start (`RUN_MIGRATIONS=true`,
   `scripts/start.sh`), inside one transaction with a PostgreSQL advisory lock.
4. If the migration fails, the API does not start → the deploy fails → the previous
   version keeps serving; the database is unchanged (the transaction rolled back).
5. Render switches traffic to the new version only once `/health/ready` returns 200.

## Rollback

- **Code only** (the common case): revert the merge commit on `main` → Render
  redeploys the previous version. The older code simply ignores the extra
  column/table, so this is safe without touching the schema.
- **Schema** (only if the new column/table itself must go, e.g. before deleting
  Render's database): run the matching downgrade SQL above, or
  `alembic downgrade <revision>` from a connection with the production
  `DATABASE_URL`. Do this only with the code already rolled back or about to be.

## Approval checklist (repeat for each migration, in order)

- [ ] Backup taken (option A) or explicitly waived (option B, demo data only)
- [ ] You have reviewed the exact SQL above and approved running it
- [ ] PR merged, CI green, Render deploy completed and healthy
- [ ] Verification steps above completed (or `scripts/smoke_test.py` run and passed)
- [ ] API version on `/openapi.json` matches what is expected
