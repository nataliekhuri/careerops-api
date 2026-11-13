"""AI career assistant: job analysis, matching, CV review, interview prep and skill insights.

Every endpoint works only on the signed-in user's own data: an application id that
belongs to someone else is reported exactly like one that does not exist.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import skills as taxonomy
from app.ai.analyzer import known_skills
from app.ai.interview_prep import PrepContext
from app.ai.providers import CareerAssistant, get_assistant
from app.api.deps import CurrentUser, DbSession, reference_not_found
from app.crud import application as application_crud
from app.crud import career_profile as profile_crud
from app.models.application import Application
from app.models.interview import Interview, InterviewOutcome
from app.schemas.ai import (
    CvReview,
    CvReviewRequest,
    Importance,
    InterviewPrep,
    JobAnalysis,
    JobSource,
    MatchResult,
    ProviderInfo,
    SkillDemand,
    SkillInsights,
    UpcomingInterview,
)
from app.schemas.career_profile import CareerProfileRead, CareerProfileUpdate

router = APIRouter(prefix="/ai", tags=["ai assistant"])
profile_router = APIRouter(prefix="/users/me/career-profile", tags=["career profile"])

Assistant = Annotated[CareerAssistant, Depends(get_assistant)]

NO_DESCRIPTION_WARNING = (
    "This application has no job description yet, so only its position and notes were analysed. "
    "Add the job posting to the application for a much better result."
)
INSIGHTS_LIMIT = 200


# ---------------------------------------------------------------- career profile


@profile_router.get("", response_model=CareerProfileRead)
def read_career_profile(user: CurrentUser, db: DbSession):
    """Your career profile (empty until you save one)."""
    return profile_crud.to_read(profile_crud.get_profile(db, user.id))


@profile_router.put("", response_model=CareerProfileRead)
def save_career_profile(data: CareerProfileUpdate, user: CurrentUser, db: DbSession):
    """Create or replace your career profile."""
    return profile_crud.to_read(profile_crud.save_profile(db, user.id, data))


# ---------------------------------------------------------------- helpers


def _resolve(
    db: Session, user_id: int, source: JobSource, assistant: CareerAssistant
) -> tuple[JobAnalysis, Application | None]:
    """Analyse the job a request points at (one of the user's applications, or pasted text)."""
    if source.application_id is None:
        return assistant.analyze_job(source.job_description or "", source.position or ""), None

    application = application_crud.get_application(db, user_id, source.application_id)
    if application is None:
        raise reference_not_found("application_id", source.application_id, "Application")
    if application.job_description.strip():
        return assistant.analyze_job(application.job_description, application.position), application
    analysis = assistant.analyze_job(application.notes, application.position)
    analysis.warnings.insert(0, NO_DESCRIPTION_WARNING)
    return analysis, application


def _upcoming(db: Session, user_id: int, application: Application | None) -> list[UpcomingInterview]:
    if application is None:
        return []
    interviews = db.scalars(
        select(Interview)
        .where(
            Interview.user_id == user_id,
            Interview.application_id == application.id,
            Interview.scheduled_at >= datetime.now(UTC),
            Interview.outcome == InterviewOutcome.PENDING.value,
        )
        .order_by(Interview.scheduled_at)
        .limit(5)
    )
    return [
        UpcomingInterview(
            id=i.id, scheduled_at=i.scheduled_at, interview_type=i.interview_type, interviewer=i.interviewer
        )
        for i in interviews
    ]


# ---------------------------------------------------------------- endpoints


@router.get("/provider", response_model=ProviderInfo)
def provider_info(user: CurrentUser, assistant: Assistant):
    """Which analyzer answers requests. The default built-in one is free and keeps data on this server."""
    return assistant.info()


@router.post("/job-analysis", response_model=JobAnalysis)
def analyze_job(source: JobSource, user: CurrentUser, db: DbSession, assistant: Assistant):
    """Extract skills (required vs. nice-to-have), seniority, experience and work mode from a job description."""
    analysis, _ = _resolve(db, user.id, source, assistant)
    return analysis


@router.post("/match", response_model=MatchResult)
def match_job(source: JobSource, user: CurrentUser, db: DbSession, assistant: Assistant):
    """Score how well your career profile fits a job (0-100), with the reasons and what to improve."""
    analysis, _ = _resolve(db, user.id, source, assistant)
    profile = profile_crud.candidate(profile_crud.get_profile(db, user.id))
    return assistant.match(profile, analysis)


@router.post("/cv-review", response_model=CvReview)
def review_cv(data: CvReviewRequest, user: CurrentUser, db: DbSession, assistant: Assistant):
    """Suggestions to improve your CV, optionally tailored to one job."""
    profile = profile_crud.candidate(profile_crud.get_profile(db, user.id))
    source = data.job_source()
    analysis = _resolve(db, user.id, source, assistant)[0] if source else None
    cv_text = data.cv_text if data.cv_text is not None else profile.cv_text
    return assistant.review_cv(cv_text, analysis, profile)


@router.post("/interview-prep", response_model=InterviewPrep)
def interview_prep(source: JobSource, user: CurrentUser, db: DbSession, assistant: Assistant):
    """Role-specific questions, your skill gaps, questions to ask and company research for one job."""
    analysis, application = _resolve(db, user.id, source, assistant)
    profile = profile_crud.candidate(profile_crud.get_profile(db, user.id))
    company = application.company_ref if application is not None else None
    context = PrepContext(
        job=analysis,
        company=application.company if application is not None else None,
        company_industry=company.industry if company else "",
        company_website=company.website if company else "",
        company_notes=company.notes if company else "",
        match=assistant.match(profile, analysis),
        upcoming=_upcoming(db, user.id, application),
    )
    return assistant.interview_prep(context)


@router.get("/skill-insights", response_model=SkillInsights)
def skill_insights(user: CurrentUser, db: DbSession, assistant: Assistant):
    """Which skills your saved job descriptions ask for most, and how many of them you cover."""
    total = db.scalar(select(func.count()).select_from(Application).where(Application.user_id == user.id))
    applications = db.scalars(
        select(Application)
        .where(Application.user_id == user.id, Application.job_description != "")
        .order_by(Application.updated_at.desc(), Application.id.desc())
        .limit(INSIGHTS_LIMIT)
    ).all()

    demand: dict[str, int] = {}
    for application in applications:
        analysis = assistant.analyze_job(application.job_description, application.position)
        for skill in analysis.skills:
            if skill.importance == Importance.REQUIRED and not taxonomy.BY_NAME[skill.name].soft:
                demand[skill.name] = demand.get(skill.name, 0) + 1

    profile = profile_crud.candidate(profile_crud.get_profile(db, user.id))
    have = known_skills(profile).names
    have |= set(taxonomy.implied_by(have))

    ranked = sorted(demand.items(), key=lambda item: (-item[1], item[0]))
    covered = sum(count for name, count in ranked if name in have)
    requested = sum(count for _, count in ranked)
    return SkillInsights(
        analyzed_applications=len(applications),
        total_applications=total or 0,
        coverage_percent=round(100 * covered / requested) if requested and have else None,
        skills=[
            SkillDemand(name=name, category=taxonomy.BY_NAME[name].category, applications=count, have=name in have)
            for name, count in ranked[:25]
        ],
        top_missing=[name for name, _ in ranked if name not in have][:5],
    )
