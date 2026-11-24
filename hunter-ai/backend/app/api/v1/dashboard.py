from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.system import DashboardSummaryRead
from app.services.dashboard_service import build_dashboard_summary

router = APIRouter(tags=["Tableau de bord"])


@router.get("/dashboard/summary", response_model=DashboardSummaryRead)
def dashboard_summary(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> DashboardSummaryRead:
    return build_dashboard_summary(db, settings)
