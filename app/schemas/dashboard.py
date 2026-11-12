from datetime import date

from pydantic import BaseModel, Field

from app.schemas.interview import InterviewRead


class WeeklyCount(BaseModel):
    week_start: date = Field(description="Monday of the week (UTC)")
    count: int


class CompanyCount(BaseModel):
    company: str
    count: int


class Rates(BaseModel):
    """Percentages (0-100) of all non-withdrawn applications, rounded to 1 decimal."""

    response_rate: float = Field(description="Reached Screening, Interview, Offer or Rejected")
    interview_rate: float = Field(description="Reached Interview or Offer")
    offer_rate: float = Field(description="Reached Offer")


class DashboardStats(BaseModel):
    total_applications: int
    active_applications: int = Field(description="Applied, Screening, Interview or Offer")
    by_status: dict[str, int]
    rates: Rates
    applications_per_week: list[WeeklyCount] = Field(description="Last 12 weeks, oldest first, zero-filled")
    top_companies: list[CompanyCount]
    total_companies: int
    total_interviews: int
    upcoming_interviews_count: int
    upcoming_interviews: list[InterviewRead] = Field(description="Next 5 pending interviews")
