from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.crud import dashboard as crud
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(user: CurrentUser, db: DbSession):
    """Your statistics: totals by status, rates, weekly activity, top companies and upcoming interviews."""
    return crud.get_stats(db, user.id)
