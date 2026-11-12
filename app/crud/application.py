from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.schemas.application import ApplicationFilters, ApplicationUpdate, JobApplication

SORT_COLUMNS = {
    "created_at": Application.created_at,
    "updated_at": Application.updated_at,
    "company": Application.company,
    "status": Application.status,
}


def create_application(db: Session, data: JobApplication) -> Application:
    application = Application(**data.model_dump(mode="json"))
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def _filtered(query: Select, filters: ApplicationFilters) -> Select:
    if filters.status is not None:
        query = query.where(Application.status == filters.status.value)
    if filters.company:
        query = query.where(Application.company.icontains(filters.company, autoescape=True))
    if filters.location:
        query = query.where(Application.location.icontains(filters.location, autoescape=True))
    return query


def list_applications(db: Session, filters: ApplicationFilters) -> tuple[list[Application], int]:
    """Return one page of applications plus the total number matching the filters."""
    total = db.scalar(_filtered(select(func.count()).select_from(Application), filters))

    descending = filters.sort.value.startswith("-")
    column = SORT_COLUMNS[filters.sort.value.lstrip("-")]
    order = column.desc() if descending else column.asc()
    tiebreak = Application.id.desc() if descending else Application.id.asc()

    query = _filtered(select(Application), filters).order_by(order, tiebreak)
    items = list(db.scalars(query.limit(filters.limit).offset(filters.offset)))
    return items, total


def get_application(db: Session, application_id: int) -> Application | None:
    return db.get(Application, application_id)


def update_application(db: Session, application: Application, data: JobApplication) -> Application:
    """Replace all editable fields (PUT)."""
    return _apply(db, application, data.model_dump(mode="json"))


def patch_application(db: Session, application: Application, data: ApplicationUpdate) -> Application:
    """Change only the fields that were sent (PATCH)."""
    return _apply(db, application, data.model_dump(mode="json", exclude_unset=True))


def _apply(db: Session, application: Application, changes: dict) -> Application:
    for field, value in changes.items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


def delete_application(db: Session, application: Application) -> None:
    db.delete(application)
    db.commit()
