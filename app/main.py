from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import applications, health
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401  (registers tables with Base)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist yet. (Alembic migrations are planned.)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CareerOps API",
    description="An API to manage job applications",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(applications.router)
