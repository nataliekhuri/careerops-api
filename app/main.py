from fastapi import FastAPI

from app.api.routes import applications, health

# The database schema is managed by Alembic migrations: run `alembic upgrade head`.

app = FastAPI(
    title="CareerOps API",
    description="An API to manage job applications",
    version="1.1.0",
)

app.include_router(health.router)
app.include_router(applications.router)
