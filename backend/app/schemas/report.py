from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Sequence

from pydantic import BaseModel, Field


class ReportRange(BaseModel):
    start: datetime | None = Field(default=None)
    end: datetime | None = Field(default=None)


class ReportTotals(BaseModel):
    income: Decimal = Field(default=0)
    expense: Decimal = Field(default=0)
    transfers: Decimal = Field(default=0)
    balance: Decimal = Field(default=0)


class ReportSummaryResponse(BaseModel):
    currency: Literal["ARS", "USD", "BTC"]
    range: ReportRange
    totals: ReportTotals
    previous_totals: ReportTotals | None = None
    budget_totals: ReportBudgetTotals | None = None


class ReportTimeseriesPoint(BaseModel):
    period: str
    income: Decimal
    expense: Decimal


class ReportTimeseriesResponse(BaseModel):
    currency: Literal["ARS", "USD", "BTC"]
    interval: Literal["month", "day"]
    points: Sequence[ReportTimeseriesPoint]


class ReportCategoryEntry(BaseModel):
    category_id: int | None
    name: str
    total: Decimal
    type: Literal["income", "expense", "transfer"]


class ReportCategoryResponse(BaseModel):
    currency: Literal["ARS", "USD", "BTC"]
    entries: Sequence[ReportCategoryEntry]


class ReportBudgetTotals(BaseModel):
    income: Decimal = Field(default=0)
    expense: Decimal = Field(default=0)
