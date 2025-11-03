from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ExchangeRateSource(Base):
    __tablename__ = "exchange_rate_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    exchange_rates = relationship("ExchangeRate", back_populates="source")


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("effective_date", "source_id", name="uq_rate_date_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("exchange_rate_sources.id"), nullable=True)
    usd_ars_oficial: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    usd_ars_blue: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    btc_usd: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    btc_ars: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    metadata_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source = relationship("ExchangeRateSource", back_populates="exchange_rates")
