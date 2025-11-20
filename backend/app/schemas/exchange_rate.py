from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class ExchangeRateValues(BaseModel):
    usd_ars_oficial: Decimal = Field(gt=0)
    usd_ars_blue: Decimal | None = Field(default=None, gt=0)
    btc_usd: Decimal = Field(gt=0)
    btc_ars: Decimal = Field(gt=0)


class ExchangeRateCreate(ExchangeRateValues):
    effective_date: date
    source_id: int | None = None
    metadata_payload: str | None = None
    is_manual: bool = False


class ExchangeRateOverride(ExchangeRateValues):
    pass


class ExchangeRateOut(ExchangeRateValues):
    id: int
    effective_date: date
    source_id: int | None
    is_manual: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExchangeRateReprocessRequest(BaseModel):
    exchange_rate_id: int | None = None
    start: datetime | None = None
    end: datetime | None = None

    @model_validator(mode="after")
    def validate_filters(self) -> "ExchangeRateReprocessRequest":
        if not any([self.exchange_rate_id, self.start, self.end]):
            raise ValueError("Indicá al menos un filtro")
        if self.start and self.end and self.end < self.start:
            raise ValueError("El rango es inválido")
        return self


class ExchangeRateReprocessResult(BaseModel):
    processed: int
    updated: int
    skipped: int
