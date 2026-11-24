"""Ventes réalisées : saisie, consultation, suppression, référence de prix (comparables)."""

import statistics
import uuid
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import ResaleRecord, SaleChannel
from app.schemas.profit import (
    ResaleRecordCreate,
    ResaleRecordPage,
    ResaleRecordRead,
    ResaleReferenceRead,
)
from app.services.audit import record_audit
from app.services.normalization import clean_text, text_key
from app.services.offer_service import NotFoundError, escape_like

MIN_COMPARABLES = 3
CENT = Decimal("0.01")


def real_profit(r: ResaleRecord) -> Decimal | None:
    if r.purchase_cost is None or r.platform_fees is None or r.shipping_paid is None:
        return None
    return r.sale_price - r.platform_fees - r.shipping_paid - r.purchase_cost


def to_read(r: ResaleRecord) -> ResaleRecordRead:
    return ResaleRecordRead(
        id=str(r.id),
        title=r.title,
        brand=r.brand,
        category=r.category,
        size=r.size,
        condition=r.condition,
        channel=r.channel.value,
        sale_price=r.sale_price,
        platform_fees=r.platform_fees,
        shipping_paid=r.shipping_paid,
        purchase_cost=r.purchase_cost,
        real_profit=real_profit(r),
        sold_on=r.sold_on,
        notes=r.notes,
        created_at=r.created_at,
    )


def create_record(db: Session, data: ResaleRecordCreate, actor: str) -> ResaleRecordRead:
    brand = clean_text(data.brand, 120)
    record = ResaleRecord(
        title=clean_text(data.title, 300) or data.title,
        brand=brand,
        brand_key=text_key(brand),
        category=clean_text(data.category, 120),
        size=clean_text(data.size, 40),
        condition=clean_text(data.condition, 40),
        channel=SaleChannel(data.channel),
        sale_price=data.sale_price,
        platform_fees=data.platform_fees,
        shipping_paid=data.shipping_paid,
        purchase_cost=data.purchase_cost,
        sold_on=data.sold_on,
        notes=clean_text(data.notes),
    )
    db.add(record)
    db.flush()
    record_audit(
        db,
        actor=actor,
        action="resale.create",
        entity_type="resale_record",
        entity_id=record.id,
        details={"brand": brand, "sale_price": str(data.sale_price), "channel": data.channel},
    )
    db.commit()
    db.refresh(record)
    return to_read(record)


def delete_record(db: Session, record_id: uuid.UUID, actor: str) -> None:
    record = db.get(ResaleRecord, record_id)
    if record is None:
        raise NotFoundError("Vente introuvable")
    db.delete(record)
    record_audit(
        db,
        actor=actor,
        action="resale.delete",
        entity_type="resale_record",
        entity_id=record_id,
        details={"title": record.title, "sale_price": str(record.sale_price)},
    )
    db.commit()


def filtered(brand: str | None, q: str | None) -> Select[ResaleRecord]:
    stmt = select(ResaleRecord)
    if brand and text_key(brand):
        stmt = stmt.where(ResaleRecord.brand_key == text_key(brand))
    if q and q.strip():
        stmt = stmt.where(ResaleRecord.title.ilike(f"%{escape_like(q.strip())}%", escape="\\"))
    return stmt


def list_records(
    db: Session, brand: str | None, q: str | None, limit: int, offset: int
) -> ResaleRecordPage:
    base = filtered(brand, q)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(ResaleRecord.sold_on.desc(), ResaleRecord.id).limit(limit).offset(offset)
    ).all()
    return ResaleRecordPage(
        items=[to_read(r) for r in rows], total=total, limit=limit, offset=offset
    )


def reference(db: Session, brand: str | None, q: str | None) -> ResaleReferenceRead:
    prices = sorted(db.scalars(filtered(brand, q).with_only_columns(ResaleRecord.sale_price)).all())
    count = len(prices)
    stats: dict[str, Decimal | None] = dict.fromkeys(
        ("minimum", "low", "median", "high", "maximum")
    )
    if count:
        stats["minimum"], stats["maximum"] = prices[0], prices[-1]
        stats["median"] = Decimal(statistics.median(prices)).quantize(CENT)
    if count >= 2:
        q1, _, q3 = statistics.quantiles(prices, n=4, method="inclusive")
        stats["low"], stats["high"] = Decimal(q1).quantize(CENT), Decimal(q3).quantize(CENT)
    return ResaleReferenceRead(
        count=count, enough=count >= MIN_COMPARABLES, brand=brand, q=q, **stats
    )
