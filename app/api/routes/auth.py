from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.crud import user as crud
from app.schemas.user import AccountDeletion, PasswordChange, Token, UserCreate, UserRead, UserUpdate

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


@auth_router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession):
    """Create an account. Emails are case-insensitive and must be unique."""
    if crud.get_user_by_email(db, data.email) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return crud.create_user(db, data)


@auth_router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    """Exchange email (sent as `username`) and password for a bearer token."""
    user = crud.authenticate(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in = create_access_token(user.id)
    return Token(access_token=token, expires_in=expires_in)


@users_router.get("/me", response_model=UserRead)
def read_me(user: CurrentUser):
    return user


@users_router.patch("/me", response_model=UserRead)
def update_me(data: UserUpdate, user: CurrentUser, db: DbSession):
    return crud.update_full_name(db, user, data.full_name)


@users_router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: PasswordChange, user: CurrentUser, db: DbSession):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    crud.set_password(db, user, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@users_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(data: AccountDeletion, user: CurrentUser, db: DbSession):
    """Permanently delete the account and all of its applications. Requires the password."""
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    crud.delete_user(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
