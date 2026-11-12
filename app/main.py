import logging

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.routes import applications, health

# The database schema is managed by Alembic migrations: run `alembic upgrade head`.

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="CareerOps API",
    description="An API to manage job applications",
    version="1.3.0",
)

register_error_handlers(app)
app.include_router(health.router)
app.include_router(applications.router)
