from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.application import Application
from app.models.interview import Interview
from app.schemas.interview import InterviewCreate, InterviewFilters, InterviewUpdate


def get_interview(db: Session, user_id: int, interview_id: int) -> Interview | None:
    """Return the interview only if it belongs to this user."""
    return db.scalar(
        select(Interview)
        .options(joinedload(Interview.application))
        .where(Interview.id == interview_id, Interview.user_id == user_id)
    )


def _filtered(query: Select, user_id: int, filters: InterviewFilters) -> Select:
    query = query.where(Interview.user_id == user_id)
    if filters.application_id is not None:
        query = query.where(Interview.application_id == filters.application_id)
    if filters.start is not None:
        query = query.where(Interview.scheduled_at >= filters.start)
    if filters.end is not None:
        query = query.where(Interview.scheduled_at < filters.end)
    if filters.outcome is not None:
        query = query.where(Interview.outcome == filters.outcome.value)
    if filters.interview_type is not None:
        query = query.where(Interview.interview_type == filters.interview_type.value)
    return query


def list_interviews(db: Session, user_id: int, filters: InterviewFilters) -> tuple[list[Interview], int]:
    total = db.scalar(_filtered(select(func.count()).select_from(Interview), user_id, filters))
    order = (
        (Interview.scheduled_at.desc(), Interview.id.desc())
        if filters.descending
        else (Interview.scheduled_at.asc(), Interview.id.asc())
    )
    query = _filtered(select(Interview).options(joinedload(Interview.application)), user_id, filters).order_by(*order)
    return list(db.scalars(query.limit(filters.limit).offset(filters.offset))), total


def create_interview(db: Session, user_id: int, application: Application, data: InterviewCreate) -> Interview:
    values = data.model_dump(mode="json", exclude={"application_id", "scheduled_at"})
    interview = Interview(user_id=user_id, application_id=application.id, scheduled_at=data.scheduled_at, **values)
    db.add(interview)
    db.commit()
    return get_interview(db, user_id, interview.id)


def update_interview(db: Session, interview: Interview, data: InterviewUpdate) -> Interview:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(interview, field, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(interview)
    return get_interview(db, interview.user_id, interview.id)


def delete_interview(db: Session, interview: Interview) -> None:
    db.delete(interview)
    db.commit()
