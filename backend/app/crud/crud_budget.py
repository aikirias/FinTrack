from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.budget import Budget, BudgetItem
from app.models.category import Category
from app.schemas.budget import BudgetCreate, BudgetUpdate


def _normalize_month(month_value: date) -> date:
    return date(month_value.year, month_value.month, 1)


def _validate_categories(db: Session, user_id: int, category_ids: Iterable[int]) -> None:
    if not category_ids:
        return
    existing = (
        db.query(Category.id)
        .filter(Category.user_id == user_id, Category.id.in_(list(category_ids)))
        .all()
    )
    existing_ids = {row.id for row in existing}
    missing = set(category_ids) - existing_ids
    if missing:
        raise ValueError(f"Categorías inválidas: {', '.join(map(str, missing))}")


def unique_constraint_violation(
    db: Session,
    user_id: int,
    month: date,
    currency_code: str,
    exclude_id: int | None = None,
) -> bool:
    query = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.month == month,
        Budget.currency_code == currency_code,
    )
    if exclude_id is not None:
        query = query.filter(Budget.id != exclude_id)
    return db.query(query.exists()).scalar()


def list_budgets(
    db: Session,
    user_id: int,
    month: date | None = None,
    currency_code: str | None = None,
) -> list[Budget]:
    query = db.query(Budget).filter(Budget.user_id == user_id)
    if month:
        query = query.filter(Budget.month == _normalize_month(month))
    if currency_code:
        query = query.filter(Budget.currency_code == currency_code.upper())
    return query.order_by(Budget.month.desc()).all()


def get_budget(db: Session, user_id: int, budget_id: int) -> Budget | None:
    return (
        db.query(Budget)
        .filter(Budget.user_id == user_id, Budget.id == budget_id)
        .first()
    )


def create_budget(db: Session, user_id: int, budget_in: BudgetCreate) -> Budget:
    if not budget_in.items:
        raise ValueError("El presupuesto debe tener al menos un ítem")
    month = _normalize_month(budget_in.month)
    currency = budget_in.currency_code.upper()

    if unique_constraint_violation(db, user_id, month, currency):
        raise ValueError("Ya existe un presupuesto para ese mes y moneda")

    _validate_categories(db, user_id, [item.category_id for item in budget_in.items])

    budget = Budget(
        user_id=user_id,
        month=month,
        currency_code=currency,
        name=budget_in.name,
    )

    for item in budget_in.items:
        budget.items.append(
            BudgetItem(
                category_id=item.category_id,
                amount=Decimal(item.amount),
            )
        )

    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def update_budget(db: Session, budget: Budget, budget_in: BudgetUpdate, user_id: int) -> Budget:
    if budget_in.name is not None:
        budget.name = budget_in.name

    if budget_in.items is not None:
        if not budget_in.items:
            raise ValueError("El presupuesto debe tener al menos un ítem")
        _validate_categories(db, user_id, [item.category_id for item in budget_in.items])
        budget.items.clear()
        for item in budget_in.items:
            budget.items.append(
                BudgetItem(
                    category_id=item.category_id,
                    amount=Decimal(item.amount),
                )
            )

    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, budget: Budget) -> None:
    db.delete(budget)
    db.commit()
