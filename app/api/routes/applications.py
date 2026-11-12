from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import ApplicationOr404, CurrentUser, DbSession, ensure_own_company
from app.crud import application as crud
from app.schemas.application import (
    ApplicationFilters,
    ApplicationMessage,
    ApplicationRead,
    ApplicationUpdate,
    JobApplication,
)

router = APIRouter(prefix="/applications", tags=["applications"])

TOTAL_COUNT_HEADER = {
    "X-Total-Count": {"description": "Total results matching the filters", "schema": {"type": "integer"}}
}


@router.post("", response_model=ApplicationMessage)
def create_application(data: JobApplication, user: CurrentUser, db: DbSession):
    ensure_own_company(db, user.id, data.company_id)
    application = crud.create_application(db, user.id, data)
    return {"message": "Application created successfully", "application": application}


@router.get("", response_model=list[ApplicationRead], responses={200: {"headers": TOTAL_COUNT_HEADER}})
def get_applications(
    response: Response, filters: Annotated[ApplicationFilters, Query()], user: CurrentUser, db: DbSession
):
    """List the current user's applications with optional filters, sorting and pagination.

    The total number of matching applications is returned in the `X-Total-Count` header.
    """
    items, total = crud.list_applications(db, user.id, filters)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application: ApplicationOr404):
    return application


@router.put("/{application_id}", response_model=ApplicationRead)
def update_application(data: JobApplication, application: ApplicationOr404, db: DbSession):
    """Replace all fields of an application (omitting `company_id` unlinks the company)."""
    ensure_own_company(db, application.user_id, data.company_id)
    return crud.update_application(db, application, data)


@router.patch("/{application_id}", response_model=ApplicationRead)
def patch_application(data: ApplicationUpdate, application: ApplicationOr404, db: DbSession):
    """Update only the fields that are sent, e.g. `{"status": "Interview"}`."""
    ensure_own_company(db, application.user_id, data.company_id)
    return crud.patch_application(db, application, data)


@router.delete("/{application_id}", response_model=ApplicationMessage)
def delete_application(application: ApplicationOr404, db: DbSession):
    deleted = ApplicationRead.model_validate(application)
    crud.delete_application(db, application)
    return {"message": "Application deleted successfully", "application": deleted}
