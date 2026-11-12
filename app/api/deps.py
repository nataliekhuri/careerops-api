"""Reusable FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import application as crud
from app.db.session import get_db
from app.models.application import Application

DbSession = Annotated[Session, Depends(get_db)]


def get_application_or_404(application_id: int, db: DbSession) -> Application:
    application = crud.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


ApplicationOr404 = Annotated[Application, Depends(get_application_or_404)]
