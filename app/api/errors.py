"""Application-wide error handling.

Unexpected errors are logged with full details on the server, but clients only
receive a generic message, so internal information (SQL, hostnames, stack traces)
is never exposed.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("careerops")


async def database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Database unavailable during %s %s: %s", request.method, request.url.path, type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "Service temporarily unavailable"})


async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error during %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(OperationalError, database_unavailable)
    app.add_exception_handler(Exception, unexpected_error)
