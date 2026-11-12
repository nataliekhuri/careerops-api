# CareerOps API

[![CI](https://github.com/nataliekhuri/careerops-api/actions/workflows/ci.yml/badge.svg)](https://github.com/nataliekhuri/careerops-api/actions/workflows/ci.yml)

A REST API for tracking job applications, built with FastAPI.

Data is stored in **PostgreSQL**, so applications persist across server restarts.

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [Pydantic](https://docs.pydantic.dev/) — request validation
- [SQLAlchemy 2](https://www.sqlalchemy.org/) — database access (ORM)
- [PostgreSQL](https://www.postgresql.org/) via [psycopg 3](https://www.psycopg.org/) — persistent storage
- [Alembic](https://alembic.sqlalchemy.org/) — database migrations
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — configuration from `.env`
- [Uvicorn](https://www.uvicorn.org/) — ASGI server
- [pytest](https://docs.pytest.org/) — automated tests, run on every push by GitHub Actions
- [Ruff](https://docs.astral.sh/ruff/) — linting and formatting
- [Docker](https://www.docker.com/) / Docker Compose — containerised API, database and migrations
- Python 3.13

## Project Structure

```
app/
├── main.py                  # creates the FastAPI app, error handlers and routes
├── core/config.py           # settings from .env / environment (DB_* or DATABASE_URL)
├── db/
│   ├── base.py              # SQLAlchemy base class
│   └── session.py           # database engine and per-request session
├── models/application.py    # "applications" database table
├── schemas/application.py   # request/response models and validation rules
├── crud/application.py      # database read/write functions
└── api/
    ├── deps.py              # shared dependencies (DB session, application lookup)
    ├── errors.py            # safe 500/503 error responses + logging
    └── routes/
        ├── health.py        # /, /health (liveness), /health/ready (readiness)
        └── applications.py  # /applications CRUD endpoints
alembic/
├── env.py                   # migration environment (app settings + migration lock)
└── versions/                # migration scripts
tests/
├── conftest.py              # fixtures: isolated test schema, rollback per test
├── test_applications.py     # CRUD, validation and error-handling tests
├── test_application_workflow.py  # statuses, timestamps, PATCH, filters, pagination
├── test_health.py
├── test_reliability.py      # readiness, database outages, unexpected errors
├── test_migrations.py       # migrations match the models, handle data, are reversible
├── test_config.py           # DB_* and DATABASE_URL settings
└── test_deploy_config.py    # render.yaml sanity checks
scripts/start.sh             # container start: optional migrations, then the API
Dockerfile                   # production image (non-root, honours $PORT)
docker-compose.yml           # db + migrate + api for local use
.github/workflows/ci.yml     # lint, tests on PostgreSQL 18, Docker build + smoke test
render.yaml                  # Render Blueprint (free web service + free PostgreSQL)
```

## Features

| Method   | Endpoint                     | Description                          |
|----------|------------------------------|--------------------------------------|
| `GET`    | `/`                          | Welcome message                      |
| `GET`    | `/health`                    | Liveness: the process is running (no database access) |
| `GET`    | `/health/ready`              | Readiness: database reachable (200) or not (503) |
| `POST`   | `/applications`              | Create a job application             |
| `GET`    | `/applications`              | List applications (filter, sort, paginate) |
| `GET`    | `/applications/{id}`         | Get one application (404 if missing) |
| `PUT`    | `/applications/{id}`         | Replace all fields (404 if missing)  |
| `PATCH`  | `/applications/{id}`         | Update only the fields sent (404 if missing) |
| `DELETE` | `/applications/{id}`         | Delete an application (404 if missing)  |

### Listing, filtering and pagination

`GET /applications` accepts these optional query parameters:

| Parameter  | Example            | Description |
|------------|--------------------|-------------|
| `status`   | `Interview`        | Exact status (case-insensitive) |
| `company`  | `acme`             | Company contains this text (case-insensitive) |
| `location` | `berlin`           | Location contains this text (case-insensitive) |
| `sort`     | `-created_at`      | `created_at`, `updated_at`, `company` or `status`; prefix `-` for descending. Default: `created_at` |
| `limit`    | `20`               | Page size, 1–100. Default: 50 |
| `offset`   | `40`               | Results to skip. Default: 0 |

The response body is a JSON list. The total number of matching applications
(ignoring `limit`/`offset`) is returned in the **`X-Total-Count`** header.

```bash
curl -i "http://127.0.0.1:8000/applications?status=interview&sort=-updated_at&limit=10"
```

### Partial updates

`PATCH` changes only the fields you send; everything else stays the same:

```bash
curl -X PATCH http://127.0.0.1:8000/applications/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Interview"}'
```

## Data Model

Each job application has the following fields:

| Field        | Type     | Required | Default     | Rules |
|--------------|----------|----------|-------------|-------|
| `id`         | int      | —        | Assigned by the server | |
| `company`    | string   | Yes      | —           | 1–255 characters |
| `position`   | string   | Yes      | —           | 1–255 characters |
| `location`   | string   | Yes      | —           | 1–255 characters |
| `status`     | string   | No       | `"Applied"` | One of the statuses below (case-insensitive) |
| `notes`      | string   | No       | `""`        | up to 5000 characters |
| `created_at` | datetime | —        | Set by the server | Read-only, ISO 8601 with time zone |
| `updated_at` | datetime | —        | Set by the server | Read-only; changes whenever a value changes |

**Statuses:** `Applied`, `Screening`, `Interview`, `Offer`, `Rejected`, `Withdrawn`.
They are enforced by both the API and a database `CHECK` constraint.

Surrounding whitespace is trimmed, blank values and `null`s are rejected, and unknown
fields are not allowed. Invalid input returns **422 Unprocessable Entity** with details
of each problem.

Example request body for `POST /applications`:

```json
{
  "company": "Acme Corp",
  "position": "Backend Developer",
  "location": "Remote",
  "status": "Applied",
  "notes": "Referred by a former colleague"
}
```

## Quick Start with Docker

Requires [Docker](https://docs.docker.com/get-docker/). This starts PostgreSQL, applies
the migrations and runs the API, using a database inside Docker (separate from any
PostgreSQL already on your machine):

```bash
cp .env.example .env      # then set DB_PASSWORD in .env
docker compose up --build
```

The API is then at `http://localhost:8000/docs`. Stop it with `docker compose down`
(add `--volumes` to also delete the Docker database).

## Getting Started (without Docker)

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

Create a dedicated database user and database (run as a PostgreSQL superuser, e.g. with `psql`):

```sql
CREATE ROLE careerops_user WITH LOGIN;
\password careerops_user
CREATE DATABASE careerops OWNER careerops_user;
```

### 4. Configure environment variables

Copy the example file and fill in your database password:

```bash
cp .env.example .env
```

| Variable      | Default          | Description            |
|---------------|------------------|------------------------|
| `DB_HOST`     | `localhost`      | PostgreSQL host        |
| `DB_PORT`     | `5433`           | PostgreSQL port        |
| `DB_NAME`     | `careerops`      | Database name          |
| `DB_USER`     | `careerops_user` | Database user          |
| `DB_PASSWORD` | —                | Database password (required) |
| `DB_CONNECT_TIMEOUT` | `5`       | Seconds to wait for a database connection |
| `DATABASE_URL` | —               | Full PostgreSQL URL; if set, it replaces the `DB_*` values (used on Render) |
| `RUN_MIGRATIONS` | `false`       | Container only: run `alembic upgrade head` before starting the API |

`.env` is listed in `.gitignore` and must never be committed.

### 5. Create the database tables

```bash
alembic upgrade head
```

> If your database already has an `applications` table created by an earlier
> version of this project, mark it as up to date instead (no data is changed):
> `alembic stamp 574c59098917`

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

### 7. Explore the API

- Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Alternative docs (ReDoc): `http://127.0.0.1:8000/redoc`

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use the database from `.env`, but run inside a temporary schema
(`test_careerops`) that is created by the migrations and dropped afterwards.
Your real data is never read or modified, and every test is rolled back.

## Code Quality

```bash
ruff check .          # lint
ruff format .         # format
```

CI runs three jobs on every pull request: **lint** (Ruff), **test** (migrations,
`alembic check` and pytest on PostgreSQL 18) and **docker** (builds the image, starts
the Compose stack and smoke-tests the running API).

## Error Handling

- Invalid input: **422** with details of each problem.
- Missing application: **404** `{"detail": "Application not found"}`.
- Database unreachable: **503** `{"detail": "Service temporarily unavailable"}`.
- Anything unexpected: **500** `{"detail": "Internal server error"}`. The full error is
  logged on the server; internal details are never sent to the client.

## Database Migrations

Schema changes are managed with Alembic:

```bash
# after changing a model in app/models/
alembic revision --autogenerate -m "describe the change"
# review the generated file in alembic/versions/, then apply it
alembic upgrade head
```

CI fails if the models and migrations get out of sync (`alembic check`).

Migrations take a PostgreSQL advisory lock, so if several instances start at once
only one applies migrations; the others wait and then find nothing to do.

## Deployment (Render)

The repository includes a [Render Blueprint](https://render.com/docs/blueprint-spec)
(`render.yaml`) that creates:

- **careerops-api**: a free Docker web service in Frankfurt, built from the `Dockerfile`.
- **careerops-db**: a free PostgreSQL 18 database, reachable only from inside Render.

### How it works

| Concern | How it's handled |
|---|---|
| Secrets | Render generates the database password and injects the connection string as `DATABASE_URL`. Nothing secret is stored in the repository. |
| Migrations | The free plan has no pre-deploy command, so the container runs `alembic upgrade head` on start (`RUN_MIGRATIONS=true`). If it fails, the API does not start, the deploy fails, and the previous version keeps serving. Each migration runs in one transaction, so a failure leaves the database unchanged. |
| Health checks | Render only routes traffic to a new deploy once `/health/ready` returns 200, meaning the app is up **and** can reach the database. |
| Deploy trigger | Automatic deploys from `main`, only after the GitHub Actions checks pass. |
| Database access | `ipAllowList: []` blocks connections from the internet. |

### Deploy it

1. Create a free account at [render.com](https://render.com) and connect your GitHub account.
2. In the Render Dashboard choose **New → Blueprint**, select this repository and the `main` branch.
3. Review the two resources (both on the **Free** plan) and click **Apply**.
4. Wait for the first deploy, then open `https://<your-service>.onrender.com/docs`.

### Free plan limitations

| Limitation | Impact on this project |
|---|---|
| Web service sleeps after **15 minutes** without traffic | The first request after a pause takes about a minute while it wakes up. |
| **750** free instance hours per workspace per month | Enough for one service running all month. Exceeding it suspends free services until the next month. |
| Free PostgreSQL **expires 30 days** after creation | After 30 days the database becomes inaccessible; after a further **14 days** Render deletes it and its data unless upgraded to a paid plan. |
| 1 GB database storage, **no backups**, one free database per workspace | Fine for a demo; do not store data you cannot lose. |
| No shell access, single instance, no persistent disk | Not needed by this app. |
| Pre-deploy command is paid-only | Migrations run at container start instead (see above). |

To keep the demo running beyond 30 days, either upgrade the database to a paid plan or
recreate the free database (the migrations rebuild the schema automatically, but existing
data is lost).

## Project Status

This project is in early development.

**Completed**

- [x] CRUD endpoints for job applications, including `PATCH` partial updates
- [x] Request validation with Pydantic (length limits, blank and unknown fields rejected)
- [x] Application status workflow, enforced in the API and the database
- [x] `created_at` / `updated_at` timestamps
- [x] Filtering, sorting and pagination
- [x] Liveness and readiness health checks
- [x] Safe error responses (no internal details leaked) and database connection timeout
- [x] PostgreSQL database for persistent storage
- [x] Configuration via environment variables (`.env`)
- [x] Database migrations with Alembic (tested for data handling and rollback)
- [x] Automated tests with pytest
- [x] Continuous integration with GitHub Actions (lint, tests, Docker smoke test)
- [x] Linting and formatting with Ruff
- [x] Docker image and Docker Compose setup

**Planned (not yet implemented)**

- [x] Deployment configuration for Render (Docker, managed PostgreSQL, migrations on start)
- [ ] Authentication (user accounts, each user sees only their own applications)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
