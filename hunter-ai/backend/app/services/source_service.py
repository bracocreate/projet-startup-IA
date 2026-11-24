"""Lecture des sources de données."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source
from app.schemas.system import SourceRead


def to_source_read(source: Source) -> SourceRead:
    return SourceRead(
        id=str(source.id),
        slug=source.slug,
        name=source.name,
        family=source.family,
        country=source.country,
        access_method=source.access_method.value,
        status=source.status.value,
        is_demo=source.is_demo,
    )


def list_sources(db: Session) -> list[SourceRead]:
    return [to_source_read(s) for s in db.scalars(select(Source).order_by(Source.name)).all()]
