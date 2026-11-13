"""Request and response models for the AI career assistant."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models.interview import InterviewType

JOB_DESCRIPTION_MAX_LENGTH = 20_000
CV_MAX_LENGTH = 30_000

JobDescriptionText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=JOB_DESCRIPTION_MAX_LENGTH)
]
CvText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=CV_MAX_LENGTH)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


# ---------------------------------------------------------------- requests


class JobSource(BaseModel):
    """Which job to analyse: one of your saved applications, or a pasted job description."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"application_id": 12},
                {"job_description": "We are hiring a Backend Engineer. Requirements: Python, FastAPI, PostgreSQL..."},
            ]
        },
    )

    application_id: int | None = Field(default=None, gt=0, description="One of your applications")
    job_description: JobDescriptionText | None = Field(default=None, description="Pasted job description")
    position: Title | None = Field(default=None, description="Job title for a pasted description (optional)")

    @model_validator(mode="after")
    def exactly_one_source(self) -> "JobSource":
        if (self.application_id is None) == (self.job_description is None):
            raise ValueError("Send either application_id or job_description")
        return self


class CvReviewRequest(BaseModel):
    """Review a CV, optionally against a job. The CV defaults to the one in your career profile."""

    model_config = ConfigDict(extra="forbid")

    cv_text: CvText | None = Field(default=None, description="CV text; defaults to your career profile CV")
    application_id: int | None = Field(default=None, gt=0, description="Tailor the review to this application")
    job_description: JobDescriptionText | None = Field(default=None, description="...or to this job description")
    position: Title | None = None

    @model_validator(mode="after")
    def at_most_one_job(self) -> "CvReviewRequest":
        if self.application_id is not None and self.job_description is not None:
            raise ValueError("Send application_id or job_description, not both")
        return self

    def job_source(self) -> JobSource | None:
        if self.application_id is None and self.job_description is None:
            return None
        return JobSource(
            application_id=self.application_id, job_description=self.job_description, position=self.position
        )


# ---------------------------------------------------------------- job analysis


class Importance(StrEnum):
    REQUIRED = "required"
    NICE_TO_HAVE = "nice_to_have"


class JobSkill(BaseModel):
    name: str
    category: str
    importance: Importance
    mentions: int = Field(description="How often the skill is mentioned")
    evidence: str = Field(description="The line of the job description where it was found")


class JobAnalysis(BaseModel):
    title: str
    role_family: str = Field(
        description="backend, frontend, fullstack, data, ml, devops, mobile, qa, security or general"
    )
    seniority: str
    min_years_experience: int | None
    work_modes: list[str] = Field(description="remote, hybrid and/or on-site, as mentioned")
    skills: list[JobSkill] = Field(description="Required skills first, then by mentions")
    required_skills: list[str]
    nice_to_have_skills: list[str]
    summary: str
    word_count: int
    warnings: list[str]


# ---------------------------------------------------------------- match


class MatchedSkill(BaseModel):
    name: str
    category: str
    importance: Importance
    credit: float = Field(description="1 = you have it, 0.5 = related experience, 0 = missing")
    reason: str


class ScoreComponent(BaseModel):
    name: str
    weight: int = Field(description="Share of the total score, in percent")
    score: float = Field(description="0-100 for this component")
    detail: str


class MatchResult(BaseModel):
    score: int | None = Field(description="0-100, or null when there is not enough information")
    level: str
    components: list[ScoreComponent]
    matched: list[MatchedSkill]
    partial: list[MatchedSkill]
    missing: list[MatchedSkill]
    explanation: list[str]
    recommendations: list[str]
    job: JobAnalysis


# ---------------------------------------------------------------- CV review


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CvCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class CvSuggestion(BaseModel):
    category: str
    priority: Priority
    title: str
    detail: str
    example: str | None = None


class KeywordCoverage(BaseModel):
    percent: int
    present: list[str]
    missing: list[str]


class CvReview(BaseModel):
    score: int | None = Field(description="Share of checks passed (0-100), or null without a CV")
    word_count: int
    sections_found: list[str]
    checks: list[CvCheck]
    keyword_coverage: KeywordCoverage | None = Field(description="Only when reviewed against a job")
    suggestions: list[CvSuggestion]


# ---------------------------------------------------------------- interview prep


class PrepQuestion(BaseModel):
    question: str
    topic: str
    tip: str


class UpcomingInterview(BaseModel):
    id: int
    scheduled_at: datetime
    interview_type: InterviewType
    interviewer: str


class InterviewPrep(BaseModel):
    title: str
    company: str | None
    role_family: str
    seniority: str
    focus_skills: list[str]
    technical_questions: list[PrepQuestion]
    behavioral_questions: list[PrepQuestion]
    gap_questions: list[PrepQuestion] = Field(description="Required skills missing from your profile")
    questions_to_ask: list[str]
    company_research: list[str]
    tips: list[str]
    upcoming_interviews: list[UpcomingInterview]


# ---------------------------------------------------------------- insights


class SkillDemand(BaseModel):
    name: str
    category: str
    applications: int = Field(description="How many of your job descriptions require it")
    have: bool


class SkillInsights(BaseModel):
    analyzed_applications: int = Field(description="Applications with a job description")
    total_applications: int
    coverage_percent: int | None = Field(description="Share of required skill demand you cover")
    skills: list[SkillDemand] = Field(description="Most requested first (top 25)")
    top_missing: list[str]


class ProviderInfo(BaseModel):
    name: str
    external: bool = Field(description="Whether requests leave this server")
    cost: str
    description: str
