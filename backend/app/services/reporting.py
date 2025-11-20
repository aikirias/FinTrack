from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from sqlalchemy import and_, case, func, literal
from sqlalchemy.orm import Session, aliased

from app.models.budget import Budget, BudgetItem
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction
from app.schemas.report import (
    ReportCategoryEntry,
    ReportCategoryResponse,
    ReportBudgetTotals,
    ReportRange,
    ReportSummaryResponse,
    ReportTimeseriesPoint,
    ReportTimeseriesResponse,
    ReportTotals,
)

CURRENCY_COLUMNS = {
    "ARS": Transaction.amount_ars,
    "USD": Transaction.amount_usd,
    "BTC": Transaction.amount_btc,
}


@dataclass
class ReportFilters:
    user_id: int
    start: datetime | None = None
    end: datetime | None = None
    account_ids: Iterable[int] | None = None
    category_ids: Iterable[int] | None = None


def _currency_column(currency: str):
    column = CURRENCY_COLUMNS.get(currency.upper())
    if column is None:
        raise ValueError("Moneda no soportada")
    return column


def _apply_filters(query, filters: ReportFilters):
    query = query.filter(Transaction.user_id == filters.user_id)
    if filters.start:
        query = query.filter(Transaction.transaction_date >= filters.start)
    if filters.end:
        query = query.filter(Transaction.transaction_date <= filters.end)
    if filters.account_ids:
        query = query.filter(Transaction.account_id.in_(filters.account_ids))
    if filters.category_ids:
        query = query.filter(Transaction.category_id.in_(filters.category_ids))
    return query


def _type_expression(cat: Category, subcat: Category):
    type_case = case((subcat.id.isnot(None), subcat.type), else_=cat.type)
    return func.coalesce(type_case, literal(CategoryType.EXPENSE.value))


def _normalize_month(value: date | datetime) -> date:
    return date(value.year, value.month, 1)


def _budget_totals(
    db: Session,
    *,
    user_id: int,
    currency: str,
    start: datetime | None,
    end: datetime | None,
) -> ReportBudgetTotals | None:
    if not start or not end:
        return None
    start_date = start.date() if isinstance(start, datetime) else start
    end_date = end.date() if isinstance(end, datetime) else end
    start_month = _normalize_month(start_date)
    end_month = _normalize_month(end_date)

    query = (
        db.query(
            Category.type.label("category_type"),
            func.coalesce(func.sum(BudgetItem.amount), 0).label("total"),
        )
        .join(Budget, BudgetItem.budget_id == Budget.id)
        .join(Category, BudgetItem.category_id == Category.id)
        .filter(
            Budget.user_id == user_id,
            Budget.currency_code == currency.upper(),
            Budget.month >= start_month,
            Budget.month <= end_month,
        )
        .group_by(Category.type)
    )

    totals = {CategoryType.INCOME.value: 0, CategoryType.EXPENSE.value: 0}
    for row in query.all():
        totals[row.category_type] = row.total

    if all(value == 0 for value in totals.values()):
        return None
    return ReportBudgetTotals(
        income=totals.get(CategoryType.INCOME.value, 0),
        expense=totals.get(CategoryType.EXPENSE.value, 0),
    )


def build_summary(
    db: Session,
    *,
    currency: str,
    filters: ReportFilters,
    previous_filters: ReportFilters | None = None,
) -> ReportSummaryResponse:
    column = _currency_column(currency)
    cat_alias = aliased(Category)
    sub_alias = aliased(Category)
    type_expression = _type_expression(cat_alias, sub_alias)

    base_query = (
        db.query(
            type_expression.label("category_type"),
            func.coalesce(func.sum(column), 0).label("total"),
        )
        .outerjoin(cat_alias, Transaction.category_id == cat_alias.id)
        .outerjoin(sub_alias, Transaction.subcategory_id == sub_alias.id)
    )
    totals = {CategoryType.INCOME.value: 0, CategoryType.EXPENSE.value: 0, CategoryType.TRANSFER.value: 0}
    for row in _apply_filters(base_query, filters).group_by(type_expression).all():
        totals[row.category_type] = row.total

    totals_model = ReportTotals(
        income=totals.get(CategoryType.INCOME.value, 0),
        expense=totals.get(CategoryType.EXPENSE.value, 0),
        transfers=totals.get(CategoryType.TRANSFER.value, 0),
        balance=totals.get(CategoryType.INCOME.value, 0) - totals.get(CategoryType.EXPENSE.value, 0),
    )

    previous_totals_model = None
    if previous_filters:
        previous_totals = {CategoryType.INCOME.value: 0, CategoryType.EXPENSE.value: 0, CategoryType.TRANSFER.value: 0}
        previous_query = (
            db.query(
                type_expression.label("category_type"),
                func.coalesce(func.sum(column), 0).label("total"),
            )
            .outerjoin(cat_alias, Transaction.category_id == cat_alias.id)
            .outerjoin(sub_alias, Transaction.subcategory_id == sub_alias.id)
        )
        for row in _apply_filters(previous_query, previous_filters).group_by(type_expression).all():
            previous_totals[row.category_type] = row.total
        previous_totals_model = ReportTotals(
            income=previous_totals.get(CategoryType.INCOME.value, 0),
            expense=previous_totals.get(CategoryType.EXPENSE.value, 0),
            transfers=previous_totals.get(CategoryType.TRANSFER.value, 0),
            balance=previous_totals.get(CategoryType.INCOME.value, 0) - previous_totals.get(CategoryType.EXPENSE.value, 0),
        )

    budget_totals = _budget_totals(
        db,
        user_id=filters.user_id,
        currency=currency,
        start=filters.start,
        end=filters.end,
    )

    return ReportSummaryResponse(
        currency=currency,
        range=ReportRange(start=filters.start, end=filters.end),
        totals=totals_model,
        previous_totals=previous_totals_model,
        budget_totals=budget_totals,
    )


def build_timeseries(
    db: Session,
    *,
    currency: str,
    filters: ReportFilters,
    interval: str = "month",
) -> ReportTimeseriesResponse:
    column = _currency_column(currency)
    cat_alias = aliased(Category)
    sub_alias = aliased(Category)
    type_expression = _type_expression(cat_alias, sub_alias)

    if interval not in {"month", "day"}:
        raise ValueError("Intervalo no soportado")

    dialect_name = db.bind.dialect.name if db.bind else "default"
    if interval == "day":
        if dialect_name == "sqlite":
            bucket = func.date(Transaction.transaction_date)
        else:
            bucket = func.date_trunc("day", Transaction.transaction_date)
    else:
        if dialect_name == "sqlite":
            bucket = func.strftime("%Y-%m-01", Transaction.transaction_date)
        else:
            bucket = func.date_trunc("month", Transaction.transaction_date)

    query = (
        db.query(
            bucket.label("bucket"),
            type_expression.label("category_type"),
            func.coalesce(func.sum(column), 0).label("total"),
        )
        .outerjoin(cat_alias, Transaction.category_id == cat_alias.id)
        .outerjoin(sub_alias, Transaction.subcategory_id == sub_alias.id)
    )
    rows = (
        _apply_filters(query, filters)
        .group_by(bucket, type_expression)
        .order_by(bucket.asc())
        .all()
    )
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0, "expense": 0})
    for row in rows:
        if isinstance(row.bucket, str):
            bucket_key = row.bucket
        else:
            bucket_key = row.bucket.date().isoformat()
        if row.category_type == CategoryType.INCOME.value:
            grouped[bucket_key]["income"] = row.total
        elif row.category_type == CategoryType.EXPENSE.value:
            grouped[bucket_key]["expense"] = row.total

    points = [
        ReportTimeseriesPoint(period=period, income=values["income"], expense=values["expense"])
        for period, values in sorted(grouped.items())
    ]

    return ReportTimeseriesResponse(currency=currency, interval=interval, points=points)


def build_category_report(
    db: Session,
    *,
    currency: str,
    filters: ReportFilters,
    category_type: CategoryType | None = None,
) -> ReportCategoryResponse:
    column = _currency_column(currency)
    cat_alias = aliased(Category)
    sub_alias = aliased(Category)
    parent_alias = aliased(Category)

    type_expression = _type_expression(cat_alias, sub_alias)
    root_category_id = case(
        (sub_alias.parent_id.isnot(None), sub_alias.parent_id),
        else_=cat_alias.id,
    )
    root_category_name = case(
        (sub_alias.parent_id.isnot(None), parent_alias.name),
        else_=cat_alias.name,
    )

    query = (
        db.query(
            root_category_id.label("category_id"),
            func.coalesce(root_category_name, literal("Sin categoría")).label("name"),
            type_expression.label("category_type"),
            func.coalesce(func.sum(column), 0).label("total"),
        )
        .outerjoin(cat_alias, Transaction.category_id == cat_alias.id)
        .outerjoin(sub_alias, Transaction.subcategory_id == sub_alias.id)
        .outerjoin(parent_alias, sub_alias.parent_id == parent_alias.id)
    )
    if category_type:
        query = query.filter(type_expression == category_type.value)

    rows = (
        _apply_filters(query, filters)
        .group_by(root_category_id, root_category_name, type_expression)
        .order_by(func.sum(column).desc())
        .all()
    )
    entries = [
        ReportCategoryEntry(
            category_id=row.category_id,
            name=row.name,
            total=row.total,
            type=row.category_type,
        )
        for row in rows
    ]
    return ReportCategoryResponse(currency=currency, entries=entries)
