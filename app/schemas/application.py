from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints, model_validator

from app.models.application import ApplicationStatus

# Limits match the database columns, so invalid input is rejected with a clear
# 422 response instead of failing inside the database with a 500 error.
NAME_MAX_LENGTH = 255
NOTES_MAX_LENGTH = 5000

RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX_LENGTH)]
NotesText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=NOTES_MAX_LENGTH)]


def _normalise_status(value: Any) -> Any:
    """Accept statuses case-insensitively, e.g. ' interview ' -> 'Interview'."""
    if isinstance(value, str):
        cleaned = value.strip().lower()
        for status in ApplicationStatus:
            if status.value.lower() == cleaned:
                return status
    return value


Status = Annotated[ApplicationStatus, BeforeValidator(_normalise_status)]

EXAMPLE = {
    "company": "Acme Corp",
    "position": "Backend Developer",
    "location": "Remote",
    "status": "Applied",
    "notes": "Referred by a former colleague",
}


class JobApplication(BaseModel):
    """Request body for creating or fully replacing an application (POST, PUT)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [EXAMPLE]})

    company: RequiredText = Field(description="Company name")
    position: RequiredText = Field(description="Job title")
    status: Status = Field(default=ApplicationStatus.APPLIED, description="Current stage of the application")
    location: RequiredText = Field(description="City, country or 'Remote'")
    notes: NotesText = Field(default="", description="Free-form notes")


class ApplicationUpdate(BaseModel):
    """Request body for a partial update (PATCH). Only the given fields change."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"status": "Interview"}]})

    company: RequiredText | None = None
    position: RequiredText | None = None
    status: Status | None = None
    location: RequiredText | None = None
    notes: NotesText | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "ApplicationUpdate":
        nulls = [name for name in self.model_fields_set if getattr(self, name) is None]
        if nulls:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(nulls))}")
        return self


class ApplicationRead(BaseModel):
    """An application as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    status: ApplicationStatus
    location: str
    notes: str
    created_at: datetime
    updated_at: datetime


class ApplicationMessage(BaseModel):
    """Response for create and delete: a message plus the application."""

    message: str
    application: ApplicationRead


class SortField(StrEnum):
    """Allowed values for the `sort` query parameter ('-' prefix = descending)."""

    CREATED_AT = "created_at"
    CREATED_AT_DESC = "-created_at"
    UPDATED_AT = "updated_at"
    UPDATED_AT_DESC = "-updated_at"
    COMPANY = "company"
    COMPANY_DESC = "-company"
    STATUS = "status"
    STATUS_DESC = "-status"


class ApplicationFilters(BaseModel):
    """Query parameters for listing applications."""

    model_config = ConfigDict(extra="forbid")

    status: Status | None = Field(default=None, description="Exact status (case-insensitive)")
    company: str | None = Field(default=None, max_length=NAME_MAX_LENGTH, description="Company contains (case-insensitive)")
    location: str | None = Field(default=None, max_length=NAME_MAX_LENGTH, description="Location contains (case-insensitive)")
    sort: SortField = Field(default=SortField.CREATED_AT, description="Sort order; prefix with '-' for descending")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of results (1-100)")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
