"""Reusable FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.crud import application as application_crud
from app.crud import company as company_crud
from app.crud import interview as interview_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.application import Application
from app.models.company import Company
from app.models.interview import Interview
from app.models.user import User

DbSession = Annotated[Session, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    try:
        user_id = decode_access_token(token)
    except TokenError:
        raise CREDENTIALS_ERROR from None
    user = user_crud.get_user(db, user_id)
    if user is None or not user.is_active:
        raise CREDENTIALS_ERROR
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_application_or_404(application_id: int, user: CurrentUser, db: DbSession) -> Application:
    # Another user's application is reported as "not found" (404, not 403), so its
    # existence is not revealed.
    application = application_crud.get_application(db, user.id, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


ApplicationOr404 = Annotated[Application, Depends(get_application_or_404)]


def get_company_or_404(company_id: int, user: CurrentUser, db: DbSession) -> Company:
    company = company_crud.get_company(db, user.id, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


CompanyOr404 = Annotated[Company, Depends(get_company_or_404)]


def get_interview_or_404(interview_id: int, user: CurrentUser, db: DbSession) -> Interview:
    interview = interview_crud.get_interview(db, user.id, interview_id)
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


InterviewOr404 = Annotated[Interview, Depends(get_interview_or_404)]


def reference_not_found(field: str, value: int, what: str) -> HTTPException:
    """422 for a body field that points at a record the user does not own (or that does not exist).

    Same message either way, so other users' ids cannot be probed.
    """
    return HTTPException(
        status_code=422,
        detail=[{"type": "not_found", "loc": ["body", field], "msg": f"{what} not found", "input": value}],
    )


def ensure_own_company(db: Session, user_id: int, company_id: int | None) -> None:
    if company_id is not None and company_crud.get_company(db, user_id, company_id) is None:
        raise reference_not_found("company_id", company_id, "Company")
