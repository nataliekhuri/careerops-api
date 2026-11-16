"""Per-user dashboard statistics, computed in SQL."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.application import Application, ApplicationStatus
from app.models.company import Company
from app.models.interview import Interview, InterviewOutcome

WEEKS = 12
ACTIVE = {ApplicationStatus.APPLIED, ApplicationStatus.SCREENING, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER}
RESPONDED = {
    ApplicationStatus.SCREENING,
    ApplicationStatus.INTERVIEW,
    ApplicationStatus.OFFER,
    ApplicationStatus.REJECTED,
}
INTERVIEWED = {ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER}


def _percent(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def get_stats(db: Session, user_id: int, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)

    counts = dict(
        db.execute(
            select(Application.status, func.count()).where(Application.user_id == user_id).group_by(Application.status)
        ).all()
    )
    by_status = {status.value: counts.get(status.value, 0) for status in ApplicationStatus}
    total = sum(by_status.values())
    considered = total - by_status[ApplicationStatus.WITHDRAWN]

    def count(statuses: set[ApplicationStatus]) -> int:
        return sum(by_status[s.value] for s in statuses)

    # Applications per week for the last 12 weeks (weeks start on Monday, UTC), zero-filled.
    this_monday = (now.astimezone(UTC).date()) - timedelta(days=now.astimezone(UTC).weekday())
    first_monday = this_monday - timedelta(weeks=WEEKS - 1)
    week = func.date_trunc("week", func.timezone("UTC", Application.created_at))
    weekly = dict(
        db.execute(
            select(func.date(week), func.count())
            .where(
                Application.user_id == user_id,
                Application.created_at >= datetime.combine(first_monday, datetime.min.time(), tzinfo=UTC),
            )
            .group_by(func.date(week))
        ).all()
    )
    per_week = [
        {"week_start": first_monday + timedelta(weeks=i), "count": weekly.get(first_monday + timedelta(weeks=i), 0)}
        for i in range(WEEKS)
    ]

    top_companies = [
        {"company": company, "count": n}
        for company, n in db.execute(
            select(Application.company, func.count().label("n"))
            .where(Application.user_id == user_id)
            .group_by(Application.company)
            .order_by(func.count().desc(), func.lower(Application.company))
            .limit(5)
        ).all()
    ]

    upcoming_filter = (
        Interview.user_id == user_id,
        Interview.scheduled_at >= now,
        Interview.outcome == InterviewOutcome.PENDING.value,
    )
    upcoming = list(
        db.scalars(
            select(Interview)
            .options(joinedload(Interview.application))
            .where(*upcoming_filter)
            .order_by(Interview.scheduled_at, Interview.id)
            .limit(5)
        )
    )

    return {
        "total_applications": total,
        "active_applications": count(ACTIVE),
        "by_status": by_status,
        "rates": {
            "response_rate": _percent(count(RESPONDED), considered),
            "interview_rate": _percent(count(INTERVIEWED), considered),
            "offer_rate": _percent(by_status[ApplicationStatus.OFFER], considered),
        },
        "applications_per_week": per_week,
        "top_companies": top_companies,
        "total_companies": db.scalar(select(func.count()).select_from(Company).where(Company.user_id == user_id)),
        "total_interviews": db.scalar(select(func.count()).select_from(Interview).where(Interview.user_id == user_id)),
        "upcoming_interviews_count": db.scalar(select(func.count()).select_from(Interview).where(*upcoming_filter)),
        "upcoming_interviews": upcoming,
    }
