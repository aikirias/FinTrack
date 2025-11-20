from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.category import CategoryType
from app.models.user import User
from app.schemas.report import (
    ReportCategoryResponse,
    ReportSummaryResponse,
    ReportTimeseriesResponse,
)
from app.services.reporting import ReportFilters, build_category_report, build_summary, build_timeseries

router = APIRouter(prefix="/reports", tags=["reports"])


def _parse_currency(value: str) -> str:
    currency = value.upper()
    if currency not in {"ARS", "USD", "BTC"}:
        raise HTTPException(status_code=400, detail="Moneda no soportada")
    return currency


@router.get("/summary", response_model=ReportSummaryResponse)
def get_summary_report(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    currency: str = Query(default="ARS"),
    account_ids: List[int] | None = Query(default=None),
    category_ids: List[int] | None = Query(default=None),
    compare_previous: bool = Query(default=True),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> ReportSummaryResponse:
    currency = _parse_currency(currency)
    filters = ReportFilters(
        user_id=current_user.id,
        start=start,
        end=end,
        account_ids=account_ids,
        category_ids=category_ids,
    )
    previous_filters = None
    if compare_previous and start and end:
        if end <= start:
            raise HTTPException(status_code=400, detail="El rango de fechas es inválido")
        duration = end - start
        previous_filters = ReportFilters(
            user_id=current_user.id,
            start=start - duration,
            end=start,
            account_ids=account_ids,
            category_ids=category_ids,
        )

    return build_summary(db, currency=currency, filters=filters, previous_filters=previous_filters)


@router.get("/timeseries", response_model=ReportTimeseriesResponse)
def get_timeseries_report(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    currency: str = Query(default="ARS"),
    interval: str = Query(default="month"),
    account_ids: List[int] | None = Query(default=None),
    category_ids: List[int] | None = Query(default=None),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> ReportTimeseriesResponse:
    currency = _parse_currency(currency)
    filters = ReportFilters(
        user_id=current_user.id,
        start=start,
        end=end,
        account_ids=account_ids,
        category_ids=category_ids,
    )
    return build_timeseries(db, currency=currency, filters=filters, interval=interval)


@router.get("/categories", response_model=ReportCategoryResponse)
def get_category_report(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    currency: str = Query(default="ARS"),
    type: CategoryType | None = Query(default=None),
    account_ids: List[int] | None = Query(default=None),
    category_ids: List[int] | None = Query(default=None),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> ReportCategoryResponse:
    currency = _parse_currency(currency)
    filters = ReportFilters(
        user_id=current_user.id,
        start=start,
        end=end,
        account_ids=account_ids,
        category_ids=category_ids,
    )
    return build_category_report(db, currency=currency, filters=filters, category_type=type)
