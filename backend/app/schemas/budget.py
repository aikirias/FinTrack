from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetItemBase(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0)


class BudgetItemCreate(BudgetItemBase):
    pass


class BudgetItemOut(BudgetItemBase):
    id: int

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    month: date
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")
    name: str | None = Field(default=None, max_length=120)


class BudgetCreate(BudgetBase):
    items: list[BudgetItemCreate]


class BudgetUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    items: list[BudgetItemCreate] | None = None


class BudgetOut(BudgetBase):
    id: int
    items: list[BudgetItemOut]

    class Config:
        from_attributes = True
