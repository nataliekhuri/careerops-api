from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyFilters, CompanyUpdate


class DuplicateCompanyNameError(Exception):
    """The user already has a company with this name (case-insensitive)."""


SORT_COLUMNS = {"name": func.lower(Company.name), "created_at": Company.created_at}


def _application_count():
    return (
        select(func.count(Application.id))
        .where(Application.company_id == Company.id, Application.user_id == Company.user_id)
        .correlate(Company)
        .scalar_subquery()
    )


def _with_count(rows) -> list[Company]:
    companies = []
    for company, count in rows:
        company.application_count = count
        companies.append(company)
    return companies


def _name_taken(db: Session, user_id: int, name: str, exclude_id: int | None = None) -> bool:
    query = select(Company.id).where(Company.user_id == user_id, func.lower(Company.name) == name.lower())
    if exclude_id is not None:
        query = query.where(Company.id != exclude_id)
    return db.scalar(query) is not None


def get_company(db: Session, user_id: int, company_id: int) -> Company | None:
    """Return the company only if it belongs to this user (with its application count)."""
    row = db.execute(
        select(Company, _application_count()).where(Company.id == company_id, Company.user_id == user_id)
    ).first()
    return _with_count([row])[0] if row else None


def _filtered(query: Select, user_id: int, filters: CompanyFilters) -> Select:
    query = query.where(Company.user_id == user_id)
    if filters.q:
        query = query.where(
            or_(
                Company.name.icontains(filters.q, autoescape=True),
                Company.industry.icontains(filters.q, autoescape=True),
                Company.location.icontains(filters.q, autoescape=True),
            )
        )
    return query


def list_companies(db: Session, user_id: int, filters: CompanyFilters) -> tuple[list[Company], int]:
    total = db.scalar(_filtered(select(func.count()).select_from(Company), user_id, filters))
    descending = filters.sort.value.startswith("-")
    column = SORT_COLUMNS[filters.sort.value.lstrip("-")]
    order = (column.desc(), Company.id.desc()) if descending else (column.asc(), Company.id.asc())
    query = _filtered(select(Company, _application_count()), user_id, filters).order_by(*order)
    rows = db.execute(query.limit(filters.limit).offset(filters.offset)).all()
    return _with_count(rows), total


def create_company(db: Session, user_id: int, data: CompanyCreate) -> Company:
    if _name_taken(db, user_id, data.name):
        raise DuplicateCompanyNameError
    company = Company(user_id=user_id, **data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    company.application_count = 0
    return company


def update_company(db: Session, company: Company, data: CompanyUpdate) -> Company:
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes and _name_taken(db, company.user_id, changes["name"], exclude_id=company.id):
        raise DuplicateCompanyNameError
    for field, value in changes.items():
        setattr(company, field, value)
    db.commit()
    return get_company(db, company.user_id, company.id)


def delete_company(db: Session, company: Company) -> None:
    """Delete the company. Linked applications are kept (their company_id becomes null)."""
    db.delete(company)
    db.commit()
