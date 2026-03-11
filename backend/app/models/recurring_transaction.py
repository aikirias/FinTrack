from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    subcategory_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_original: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_type: Mapped[str] = mapped_column(String(20), default="official")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # daily | weekly | monthly | yearly
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    next_run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    last_run_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User")
    account = relationship("Account")
    category = relationship("Category", foreign_keys=[category_id])
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
