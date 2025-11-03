from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExchangeRateValues(BaseModel):
    usd_ars_oficial: Decimal = Field(gt=0)
    usd_ars_blue: Decimal | None = Field(default=None, gt=0)
    btc_usd: Decimal = Field(gt=0)
    btc_ars: Decimal = Field(gt=0)


class ExchangeRateCreate(ExchangeRateValues):
    effective_date: date
    source_id: int | None = None
    metadata_payload: str | None = None


class ExchangeRateOverride(ExchangeRateValues):
    pass


class ExchangeRateOut(ExchangeRateValues):
    id: int
    effective_date: date
    source_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
