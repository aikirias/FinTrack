from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.exchange_rate import ExchangeRateOverride, ExchangeRateOut


class TransactionBase(BaseModel):
    transaction_date: datetime
    account_id: int
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")
    amount_original: Decimal
    category_id: int | None = None
    subcategory_id: int | None = None
    notes: str | None = Field(default=None, max_length=500)
    rate_type: Literal["official", "blue"] = "official"


class TransactionCreate(TransactionBase):
    exchange_rate_id: int | None = None
    manual_rates: ExchangeRateOverride | None = None


class TransactionUpdate(BaseModel):
    transaction_date: datetime | None = None
    account_id: int | None = None
    currency_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    amount_original: Decimal | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    notes: str | None = Field(default=None, max_length=500)
    rate_type: Literal["official", "blue"] | None = None
    exchange_rate_id: int | None = None
    manual_rates: ExchangeRateOverride | None = None


class TransactionOut(TransactionBase):
    id: int
    amount_ars: Decimal
    amount_usd: Decimal
    amount_btc: Decimal
    exchange_rate_id: int | None
    exchange_rate: ExchangeRateOut | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
