from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import CompanyOr404, CurrentUser, DbSession
from app.api.routes.applications import TOTAL_COUNT_HEADER
from app.crud import company as crud
from app.schemas.company import CompanyCreate, CompanyFilters, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])

DUPLICATE = HTTPException(status_code=409, detail="You already have a company with this name")


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(data: CompanyCreate, user: CurrentUser, db: DbSession):
    try:
        return crud.create_company(db, user.id, data)
    except crud.DuplicateCompanyNameError:
        raise DUPLICATE from None


@router.get("", response_model=list[CompanyRead], responses={200: {"headers": TOTAL_COUNT_HEADER}})
def list_companies(response: Response, filters: Annotated[CompanyFilters, Query()], user: CurrentUser, db: DbSession):
    """List your companies with search, sorting and pagination (total in `X-Total-Count`)."""
    items, total = crud.list_companies(db, user.id, filters)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company: CompanyOr404):
    return company


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(data: CompanyUpdate, company: CompanyOr404, db: DbSession):
    try:
        return crud.update_company(db, company, data)
    except crud.DuplicateCompanyNameError:
        raise DUPLICATE from None


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company: CompanyOr404, db: DbSession):
    """Delete a company. Applications linked to it are kept and simply unlinked."""
    crud.delete_company(db, company)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
