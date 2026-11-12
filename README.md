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
- Python 3.13

## Project Structure

```
app/
├── main.py                  # creates the FastAPI app and includes routes
├── core/config.py           # settings loaded from .env
├── db/
│   ├── base.py              # SQLAlchemy base class
│   └── session.py           # database engine and per-request session
├── models/application.py    # "applications" database table
├── schemas/application.py   # request/response models and validation rules
├── crud/application.py      # database read/write functions
└── api/routes/
    ├── health.py            # / and /health
    └── applications.py      # /applications CRUD endpoints
alembic/
├── env.py                   # migration environment (reads DB settings from .env)
└── versions/                # migration scripts
tests/
├── conftest.py              # fixtures: isolated test schema, rollback per test
├── test_applications.py     # CRUD, validation and error-handling tests
├── test_health.py
└── test_migrations.py       # migrations match the models and are reversible
.github/workflows/ci.yml     # runs migrations + tests against PostgreSQL 18
```

## Features

| Method   | Endpoint                     | Description                          |
|----------|------------------------------|--------------------------------------|
| `GET`    | `/`                          | Welcome message                      |
| `GET`    | `/health`                    | Health check                         |
| `POST`   | `/applications`              | Create a job application             |
| `GET`    | `/applications`              | List all job applications            |
| `GET`    | `/applications/{id}`         | Get one application (404 if missing) |
| `PUT`    | `/applications/{id}`         | Replace an application (404 if missing) |
| `DELETE` | `/applications/{id}`         | Delete an application (404 if missing)  |

## Data Model

Each job application has the following fields:

| Field      | Type   | Required | Default     | Rules |
|------------|--------|----------|-------------|-------|
| `id`       | int    | —        | Assigned by the server | |
| `company`  | string | Yes      | —           | 1–255 characters |
| `position` | string | Yes      | —           | 1–255 characters |
| `location` | string | Yes      | —           | 1–255 characters |
| `status`   | string | No       | `"Applied"` | 1–50 characters |
| `notes`    | string | No       | `""`        | up to 5000 characters |

Surrounding whitespace is trimmed, blank values are rejected, and unknown fields are
not allowed. Invalid input returns **422 Unprocessable Entity** with details of each problem.

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

## Getting Started

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

## Database Migrations

Schema changes are managed with Alembic:

```bash
# after changing a model in app/models/
alembic revision --autogenerate -m "describe the change"
# review the generated file in alembic/versions/, then apply it
alembic upgrade head
```

CI fails if the models and migrations get out of sync (`alembic check`).

## Project Status

This project is in early development.

**Completed**

- [x] CRUD endpoints for job applications
- [x] Request validation with Pydantic (length limits, blank and unknown fields rejected)
- [x] Health check endpoint
- [x] PostgreSQL database for persistent storage
- [x] Configuration via environment variables (`.env`)
- [x] Database migrations with Alembic
- [x] Automated tests with pytest
- [x] Continuous integration with GitHub Actions

**Planned (not yet implemented)**

- [ ] Application status workflow (fixed set of statuses) and timestamps
- [ ] Filtering, search and pagination
- [ ] Authentication
- [ ] Docker setup

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
