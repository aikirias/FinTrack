from datetime import date, datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_budget
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetItemOut, BudgetOut, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["budgets"])

_CURRENCY_COLUMN = {
    "ARS": Transaction.amount_ars,
    "USD": Transaction.amount_usd,
    "BTC": Transaction.amount_btc,
}


def _parse_month(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fecha inválida") from exc
    return date(parsed.year, parsed.month, 1)


def _compute_actuals(
    db: Session,
    *,
    user_id: int,
    month: date,
    currency_code: str,
    category_ids: list[int],
) -> dict[int, Decimal]:
    """Return {category_id: actual_spent} for the given month/currency."""
    col = _CURRENCY_COLUMN.get(currency_code.upper())
    if col is None or not category_ids:
        return {}

    start = datetime(month.year, month.month, 1)
    if month.month == 12:
        end = datetime(month.year + 1, 1, 1)
    else:
        end = datetime(month.year, month.month + 1, 1)

    rows = (
        db.query(Transaction.category_id, func.coalesce(func.sum(col), 0).label("total"))
        .filter(
            Transaction.user_id == user_id,
            Transaction.category_id.in_(category_ids),
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
        )
        .group_by(Transaction.category_id)
        .all()
    )
    return {row.category_id: Decimal(str(row.total)) for row in rows}


@router.get("/", response_model=List[BudgetOut])
def list_budgets(
    month: str | None = Query(default=None),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> List[BudgetOut]:
    month_value = _parse_month(month)
    currency_upper = currency.upper() if currency else None
    budgets = crud_budget.list_budgets(
        db,
        user_id=current_user.id,
        month=month_value,
        currency_code=currency_upper,
    )

    result: list[BudgetOut] = []
    for budget in budgets:
        cat_ids = [item.category_id for item in budget.items]
        actuals: dict[int, Decimal] = {}
        if month_value and currency_upper:
            actuals = _compute_actuals(
                db,
                user_id=current_user.id,
                month=budget.month,
                currency_code=budget.currency_code,
                category_ids=cat_ids,
            )
        items_out = [
            BudgetItemOut(
                id=item.id,
                category_id=item.category_id,
                amount=item.amount,
                actual_amount=actuals.get(item.category_id),
            )
            for item in budget.items
        ]
        out = BudgetOut.model_validate(budget)
        out.items = items_out
        result.append(out)
    return result


@router.post("/", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: BudgetCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> BudgetOut:
    try:
        budget = crud_budget.create_budget(db, user_id=current_user.id, budget_in=budget_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BudgetOut.model_validate(budget)


@router.patch("/{budget_id}", response_model=BudgetOut)
def update_budget(
    budget_id: int,
    budget_in: BudgetUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> BudgetOut:
    budget = crud_budget.get_budget(db, current_user.id, budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presupuesto no encontrado")
    try:
        updated = crud_budget.update_budget(db, budget=budget, budget_in=budget_in, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BudgetOut.model_validate(updated)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> None:
    budget = crud_budget.get_budget(db, current_user.id, budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presupuesto no encontrado")
    crud_budget.delete_budget(db, budget)
