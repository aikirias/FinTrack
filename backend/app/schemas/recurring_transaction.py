from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


Frequency = Literal["daily", "weekly", "monthly", "yearly"]


class RecurringTransactionBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    account_id: int | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    amount_original: Decimal = Field(gt=0)
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")
    rate_type: Literal["official", "blue"] = "official"
    notes: str | None = Field(default=None, max_length=500)
    frequency: Frequency
    next_run_date: date


class RecurringTransactionCreate(RecurringTransactionBase):
    pass


class RecurringTransactionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    account_id: int | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    amount_original: Decimal | None = Field(default=None, gt=0)
    currency_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    rate_type: Literal["official", "blue"] | None = None
    notes: str | None = Field(default=None, max_length=500)
    frequency: Frequency | None = None
    next_run_date: date | None = None
    is_active: bool | None = None


class RecurringTransactionOut(RecurringTransactionBase):
    id: int
    is_active: bool
    last_run_date: date | None
    created_at: datetime

    class Config:
        from_attributes = True
