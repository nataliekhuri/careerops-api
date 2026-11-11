# CareerOps API

A REST API for tracking job applications, built with FastAPI.

Data is stored in **PostgreSQL**, so applications persist across server restarts.

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [Pydantic](https://docs.pydantic.dev/) — request validation
- [SQLAlchemy 2](https://www.sqlalchemy.org/) — database access (ORM)
- [PostgreSQL](https://www.postgresql.org/) via [psycopg 3](https://www.psycopg.org/) — persistent storage
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — configuration from `.env`
- [Uvicorn](https://www.uvicorn.org/) — ASGI server
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
├── schemas/application.py   # request/response models
├── crud/application.py      # database read/write functions
└── api/routes/
    ├── health.py            # / and /health
    └── applications.py      # /applications CRUD endpoints
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

| Field      | Type   | Required | Default     |
|------------|--------|----------|-------------|
| `id`       | int    | —        | Assigned by the server |
| `company`  | string | Yes      | —           |
| `position` | string | Yes      | —           |
| `location` | string | Yes      | —           |
| `status`   | string | No       | `"Applied"` |
| `notes`    | string | No       | `""`        |

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

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

The `applications` table is created automatically on first start.
The API runs at `http://127.0.0.1:8000`.

### 6. Explore the API

- Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Alternative docs (ReDoc): `http://127.0.0.1:8000/redoc`

## Project Status

This project is in early development.

**Completed**

- [x] CRUD endpoints for job applications
- [x] Request validation with Pydantic
- [x] Health check endpoint
- [x] PostgreSQL database for persistent storage
- [x] Configuration via environment variables (`.env`)

**Planned (not yet implemented)**

- [ ] Database migrations with Alembic
- [ ] Authentication
- [ ] Automated tests
- [ ] Docker setup

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
