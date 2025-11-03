from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_exchange_rate
from app.db.session import get_db
from app.models.exchange_rate import ExchangeRate
from app.models.user import User
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateOut
from app.services.exchange_rates import ensure_daily_exchange_rate

router = APIRouter(prefix="/exchange-rates", tags=["exchange_rates"])


@router.get("/latest", response_model=ExchangeRateOut)
def latest_rate(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeRateOut:
    rate = ensure_daily_exchange_rate(db)
    return ExchangeRateOut.model_validate(rate)


@router.post("/override", response_model=ExchangeRateOut, status_code=status.HTTP_201_CREATED)
def override_rate(
    rate_in: ExchangeRateCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeRateOut:
    existing = crud_exchange_rate.get_rate_by_date(db, rate_in.effective_date)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una cotización para esa fecha")

    rate = crud_exchange_rate.create_exchange_rate(db, rate_in)
    return ExchangeRateOut.model_validate(rate)
