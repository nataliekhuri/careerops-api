from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

Password = Annotated[str, Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


def _check_password_strength(value: str) -> str:
    if not value.strip():
        raise ValueError("Password cannot be blank")
    if value.isdigit() or value.isalpha():
        raise ValueError("Password must contain both letters and numbers or symbols")
    return value


class UserCreate(BaseModel):
    """Registration request."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"email": "ann@example.com", "password": "correct-horse-7", "full_name": "Ann"}]
        },
    )

    email: EmailStr
    password: Password
    full_name: FullName = ""

    _strength = field_validator("password")(_check_password_strength)


class UserRead(BaseModel):
    """A user as returned by the API (never includes the password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    created_at: datetime


class UserUpdate(BaseModel):
    """Profile changes."""

    model_config = ConfigDict(extra="forbid")

    full_name: FullName


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(max_length=PASSWORD_MAX_LENGTH)
    new_password: Password

    _strength = field_validator("new_password")(_check_password_strength)


class AccountDeletion(BaseModel):
    """Deleting an account requires the current password."""

    model_config = ConfigDict(extra="forbid")

    password: str = Field(max_length=PASSWORD_MAX_LENGTH)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until the token expires")
