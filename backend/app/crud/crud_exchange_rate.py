from datetime import date

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import ExchangeRateCreate


def get_exchange_rate(db: Session, rate_id: int) -> ExchangeRate | None:
    return db.get(ExchangeRate, rate_id)


def get_latest_rate(db: Session) -> ExchangeRate | None:
    return db.query(ExchangeRate).order_by(desc(ExchangeRate.effective_date)).first()


def get_rate_by_date(db: Session, effective_date: date) -> ExchangeRate | None:
    return (
        db.query(ExchangeRate)
        .filter(ExchangeRate.effective_date == effective_date)
        .order_by(desc(ExchangeRate.created_at))
        .first()
    )


def create_exchange_rate(db: Session, rate_in: ExchangeRateCreate) -> ExchangeRate:
    exchange_rate = ExchangeRate(
        effective_date=rate_in.effective_date,
        source_id=rate_in.source_id,
        usd_ars_oficial=rate_in.usd_ars_oficial,
        usd_ars_blue=rate_in.usd_ars_blue,
        btc_usd=rate_in.btc_usd,
        btc_ars=rate_in.btc_ars,
        is_manual=rate_in.is_manual,
        metadata_payload=rate_in.metadata_payload,
    )
    db.add(exchange_rate)
    db.commit()
    db.refresh(exchange_rate)
    return exchange_rate
