"""Reusable FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.crud import application as application_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.application import Application
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
