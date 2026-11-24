from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.system import SourceRead
from app.services.source_service import list_sources

router = APIRouter(tags=["Sources"])


@router.get("/sources", response_model=list[SourceRead])
def read_sources(db: Session = Depends(get_db)) -> list[SourceRead]:
    return list_sources(db)
