from datetime import datetime
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints, model_validator

from app.models.application import ApplicationStatus
from app.models.interview import InterviewOutcome, InterviewType

Location = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Interviewer = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]
Duration = Annotated[int, Field(ge=1, le=600, description="Minutes (1-600)")]


def _lower(value: Any) -> Any:
    return value.strip().lower() if isinstance(value, str) else value


Type = Annotated[InterviewType, BeforeValidator(_lower)]
Outcome = Annotated[InterviewOutcome, BeforeValidator(_lower)]


class InterviewCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "application_id": 1,
                    "scheduled_at": "2026-12-01T14:00:00+01:00",
                    "duration_minutes": 45,
                    "interview_type": "video",
                    "location": "https://meet.example/abc",
                    "interviewer": "Jane Doe, Engineering Manager",
                    "notes": "Prepare system design examples",
                }
            ]
        },
    )

    application_id: int = Field(gt=0)
    scheduled_at: AwareDatetime = Field(description="Date and time including a time zone offset")
    duration_minutes: Duration = 60
    interview_type: Type = InterviewType.VIDEO
    location: Location = Field(default="", description="Address or meeting link")
    interviewer: Interviewer = ""
    notes: Notes = ""
    outcome: Outcome = InterviewOutcome.PENDING


class InterviewUpdate(BaseModel):
    """Partial update. The application cannot be changed; create a new interview instead."""

    model_config = ConfigDict(extra="forbid")

    scheduled_at: AwareDatetime | None = None
    duration_minutes: Duration | None = None
    interview_type: Type | None = None
    location: Location | None = None
    interviewer: Interviewer | None = None
    notes: Notes | None = None
    outcome: Outcome | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "InterviewUpdate":
        nulls = [name for name in self.model_fields_set if getattr(self, name) is None]
        if nulls:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(nulls))}")
        return self


class ApplicationSummary(BaseModel):
    """Just enough about the application to show an interview in a calendar."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    status: ApplicationStatus


class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    application: ApplicationSummary
    scheduled_at: datetime
    duration_minutes: int
    interview_type: InterviewType
    location: str
    interviewer: str
    notes: str
    outcome: InterviewOutcome
    created_at: datetime
    updated_at: datetime


class InterviewFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: int | None = Field(default=None, gt=0)
    start: AwareDatetime | None = Field(default=None, description="Only interviews at or after this time")
    end: AwareDatetime | None = Field(default=None, description="Only interviews before this time")
    outcome: Outcome | None = None
    interview_type: Type | None = None
    descending: bool = Field(default=False, description="Newest first instead of soonest first")
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def start_before_end(self) -> "InterviewFilters":
        if self.start and self.end and self.start >= self.end:
            raise ValueError("start must be before end")
        return self
