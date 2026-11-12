from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Website = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Industry = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
Location = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]


def _check_website(value: str | None) -> str | None:
    """Websites are optional, but if given must be http(s) links."""
    if value and not value.lower().startswith(("http://", "https://")):
        raise ValueError("Website must start with http:// or https://")
    return value


class CompanyCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Acme Corp",
                    "website": "https://acme.example",
                    "industry": "Software",
                    "location": "Berlin",
                    "notes": "Great engineering blog",
                }
            ]
        },
    )

    name: Name
    website: Website = ""
    industry: Industry = ""
    location: Location = ""
    notes: Notes = ""

    _website = field_validator("website")(_check_website)


class CompanyUpdate(BaseModel):
    """Partial update: only the fields sent change."""

    model_config = ConfigDict(extra="forbid")

    name: Name | None = None
    website: Website | None = None
    industry: Industry | None = None
    location: Location | None = None
    notes: Notes | None = None

    _website = field_validator("website")(_check_website)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "CompanyUpdate":
        nulls = [name for name in self.model_fields_set if getattr(self, name) is None]
        if nulls:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(nulls))}")
        return self


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website: str
    industry: str
    location: str
    notes: str
    application_count: int = 0
    created_at: datetime
    updated_at: datetime


class CompanySort(StrEnum):
    NAME = "name"
    NAME_DESC = "-name"
    CREATED_AT = "created_at"
    CREATED_AT_DESC = "-created_at"


class CompanyFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str | None = Field(default=None, max_length=255, description="Name, industry or location contains (any case)")
    sort: CompanySort = Field(default=CompanySort.NAME)
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
