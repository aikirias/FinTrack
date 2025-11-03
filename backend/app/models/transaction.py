from datetime import datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    subcategory_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    exchange_rate_id: Mapped[int | None] = mapped_column(ForeignKey("exchange_rates.id"), nullable=True)

    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_type: Mapped[str] = mapped_column(String(20), default="official")
    amount_original: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    amount_ars: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    amount_btc: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", foreign_keys=[category_id], back_populates="transactions")
    subcategory = relationship(
        "Category", foreign_keys=[subcategory_id], back_populates="subcategory_transactions"
    )
    exchange_rate = relationship("ExchangeRate")
