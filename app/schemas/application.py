from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Limits match the database columns, so invalid input is rejected with a clear
# 422 response instead of failing inside the database with a 500 error.
NAME_MAX_LENGTH = 255
STATUS_MAX_LENGTH = 50
NOTES_MAX_LENGTH = 5000

RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX_LENGTH)]
StatusText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=STATUS_MAX_LENGTH)]
NotesText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=NOTES_MAX_LENGTH)]


class JobApplication(BaseModel):
    """Request body for creating or replacing an application."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "company": "Acme Corp",
                    "position": "Backend Developer",
                    "location": "Remote",
                    "status": "Applied",
                    "notes": "Referred by a former colleague",
                }
            ]
        },
    )

    company: RequiredText = Field(description="Company name")
    position: RequiredText = Field(description="Job title")
    status: StatusText = Field(default="Applied", description="Current stage of the application")
    location: RequiredText = Field(description="City, country or 'Remote'")
    notes: NotesText = Field(default="", description="Free-form notes")


class ApplicationRead(BaseModel):
    """An application as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    status: str
    location: str
    notes: str


class ApplicationMessage(BaseModel):
    """Response for create and delete: a message plus the application."""

    message: str
    application: ApplicationRead
