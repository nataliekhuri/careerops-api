import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.routes import ai, applications, auth, companies, dashboard, health, interviews
from app.core.config import get_settings

# The database schema is managed by Alembic migrations: run `alembic upgrade head`.

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Refuse to start without a signing key, rather than failing on the first login.
    if get_settings().jwt_secret_key is None:
        raise RuntimeError("JWT_SECRET_KEY is not set. See .env.example.")
    yield


app = FastAPI(
    title="CareerOps API",
    description="Track job applications. Register, log in, then use the bearer token on every request.",
    version="2.2.0",
    lifespan=lifespan,
)

settings = get_settings()
if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Total-Count"],
    )

register_error_handlers(app)
app.include_router(health.router)
app.include_router(auth.auth_router)
app.include_router(auth.users_router)
app.include_router(applications.router)
app.include_router(companies.router)
app.include_router(interviews.router)
app.include_router(dashboard.router)
app.include_router(ai.profile_router)
app.include_router(ai.router)
