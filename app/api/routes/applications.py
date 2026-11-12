from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.crud import application as crud
from app.db.session import get_db
from app.models.application import Application
from app.schemas.application import (
    ApplicationFilters,
    ApplicationMessage,
    ApplicationRead,
    ApplicationUpdate,
    JobApplication,
)

router = APIRouter(prefix="/applications", tags=["applications"])


def get_application_or_404(application_id: int, db: Session = Depends(get_db)) -> Application:
    application = crud.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("", response_model=ApplicationMessage)
def create_application(data: JobApplication, db: Session = Depends(get_db)):
    application = crud.create_application(db, data)
    return {"message": "Application created successfully", "application": application}


@router.get(
    "",
    response_model=list[ApplicationRead],
    responses={200: {"headers": {"X-Total-Count": {"description": "Total results matching the filters", "schema": {"type": "integer"}}}}},
)
def get_applications(
    response: Response,
    filters: Annotated[ApplicationFilters, Query()],
    db: Session = Depends(get_db),
):
    """List applications with optional filters, sorting and pagination.

    The total number of matching applications is returned in the `X-Total-Count` header.
    """
    items, total = crud.list_applications(db, filters)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application: Application = Depends(get_application_or_404)):
    return application


@router.put("/{application_id}", response_model=ApplicationRead)
def update_application(
    data: JobApplication,
    application: Application = Depends(get_application_or_404),
    db: Session = Depends(get_db),
):
    """Replace all fields of an application."""
    return crud.update_application(db, application, data)


@router.patch("/{application_id}", response_model=ApplicationRead)
def patch_application(
    data: ApplicationUpdate,
    application: Application = Depends(get_application_or_404),
    db: Session = Depends(get_db),
):
    """Update only the fields that are sent, e.g. `{"status": "Interview"}`."""
    return crud.patch_application(db, application, data)


@router.delete("/{application_id}", response_model=ApplicationMessage)
def delete_application(
    application: Application = Depends(get_application_or_404),
    db: Session = Depends(get_db),
):
    deleted = ApplicationRead.model_validate(application)
    crud.delete_application(db, application)
    return {"message": "Application deleted successfully", "application": deleted}
