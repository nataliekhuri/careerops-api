from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession, InterviewOr404, reference_not_found
from app.api.routes.applications import TOTAL_COUNT_HEADER
from app.crud import application as application_crud
from app.crud import interview as crud
from app.schemas.interview import InterviewCreate, InterviewFilters, InterviewRead, InterviewUpdate

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
def create_interview(data: InterviewCreate, user: CurrentUser, db: DbSession):
    """Schedule an interview for one of your applications."""
    application = application_crud.get_application(db, user.id, data.application_id)
    if application is None:
        raise reference_not_found("application_id", data.application_id, "Application")
    return crud.create_interview(db, user.id, application, data)


@router.get("", response_model=list[InterviewRead], responses={200: {"headers": TOTAL_COUNT_HEADER}})
def list_interviews(
    response: Response, filters: Annotated[InterviewFilters, Query()], user: CurrentUser, db: DbSession
):
    """List your interviews, soonest first. Use `start`/`end` for a calendar range (total in `X-Total-Count`)."""
    items, total = crud.list_interviews(db, user.id, filters)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{interview_id}", response_model=InterviewRead)
def get_interview(interview: InterviewOr404):
    return interview


@router.patch("/{interview_id}", response_model=InterviewRead)
def update_interview(data: InterviewUpdate, interview: InterviewOr404, db: DbSession):
    """Reschedule, record the outcome, or edit details."""
    return crud.update_interview(db, interview, data)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(interview: InterviewOr404, db: DbSession):
    crud.delete_interview(db, interview)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
