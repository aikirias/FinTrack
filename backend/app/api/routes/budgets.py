from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_budget
from app.db.session import get_db
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetOut, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _parse_month(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fecha inválida") from exc
    return date(parsed.year, parsed.month, 1)


@router.get("/", response_model=List[BudgetOut])
def list_budgets(
    month: str | None = Query(default=None),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> List[BudgetOut]:
    month_value = _parse_month(month)
    budgets = crud_budget.list_budgets(
        db,
        user_id=current_user.id,
        month=month_value,
        currency_code=currency.upper() if currency else None,
    )
    return [BudgetOut.model_validate(budget) for budget in budgets]


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
