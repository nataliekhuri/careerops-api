from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.ai import CvText

Short = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
SkillName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
MAX_SKILLS = 100


class CareerProfileUpdate(BaseModel):
    """Your career profile (replaces the stored one). Used by the AI assistant only."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "headline": "Backend developer",
                    "target_role": "Backend Engineer",
                    "years_experience": 3,
                    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                    "cv_text": "Experience\n- Built a FastAPI service...",
                }
            ]
        },
    )

    headline: Short = ""
    target_role: Short = ""
    years_experience: int | None = Field(default=None, ge=0, le=60)
    skills: list[SkillName] = Field(default_factory=list, max_length=MAX_SKILLS)
    cv_text: CvText = ""

    @field_validator("skills")
    @classmethod
    def unique_skills(cls, skills: list[str]) -> list[str]:
        """Drop duplicates (case-insensitive), keeping the first spelling and the order."""
        seen: set[str] = set()
        unique = []
        for skill in skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique.append(skill)
        return unique


class CareerProfileRead(BaseModel):
    headline: str
    target_role: str
    years_experience: int | None
    skills: list[str]
    cv_text: str
    recognized_skills: list[str] = Field(description="Skills the assistant understands (from skills and CV)")
    unrecognized_skills: list[str] = Field(description="Entered skills that are not in the skill list (not scored)")
    updated_at: datetime | None = Field(description="null until the profile is saved for the first time")
