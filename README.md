# CareerOps API

A REST API for tracking job applications, built with FastAPI.

> **Note:** The current version stores data in **temporary in-memory storage** (a Python list).
> All data is lost whenever the server restarts. Persistent storage with PostgreSQL is planned.

## Tech Stack

**Current**

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [Pydantic](https://docs.pydantic.dev/) — request validation
- [Uvicorn](https://www.uvicorn.org/) — ASGI server
- Python 3.13

**Planned**

- PostgreSQL — persistent database

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

### 3. Run the server

```bash
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

### 4. Explore the API

- Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Alternative docs (ReDoc): `http://127.0.0.1:8000/redoc`

## Project Status

This project is in early development.

**Completed**

- [x] CRUD endpoints for job applications
- [x] Request validation with Pydantic
- [x] Health check endpoint
- [x] Temporary in-memory storage

**Planned (not yet implemented)**

- [ ] PostgreSQL database for persistent storage
- [ ] Authentication
- [ ] Automated tests
- [ ] Docker setup
