import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession

router = APIRouter(tags=["health"])
logger = logging.getLogger("careerops")


@router.get("/")
def home():
    return {
        "message": "Welcome to CareerOps API!",
        "status": "running",
    }


@router.get("/health")
def health_check():
    """Liveness: the process is up. Does not touch the database."""
    return {"status": "healthy"}


@router.get(
    "/health/ready",
    responses={503: {"description": "Database unreachable", "content": {"application/json": {}}}},
)
def readiness_check(db: DbSession):
    """Readiness: the API can reach its database and is ready for traffic."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Readiness check failed: database unreachable (%s)", type(exc).__name__)
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unreachable"})
    return {"status": "ready", "database": "ok"}
