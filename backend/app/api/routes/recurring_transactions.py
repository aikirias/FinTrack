from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_recurring_transaction
from app.db.session import get_db
from app.models.user import User
from app.schemas.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionOut,
    RecurringTransactionUpdate,
)

router = APIRouter(prefix="/recurring-transactions", tags=["recurring-transactions"])


@router.get("/", response_model=List[RecurringTransactionOut])
def list_recurring(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> List[RecurringTransactionOut]:
    items = crud_recurring_transaction.list_recurring(db, current_user.id)
    return [RecurringTransactionOut.model_validate(rt) for rt in items]


@router.post("/", response_model=RecurringTransactionOut, status_code=status.HTTP_201_CREATED)
def create_recurring(
    rt_in: RecurringTransactionCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTransactionOut:
    rt = crud_recurring_transaction.create_recurring(db, current_user.id, rt_in)
    return RecurringTransactionOut.model_validate(rt)


@router.patch("/{recurring_id}", response_model=RecurringTransactionOut)
def update_recurring(
    recurring_id: int,
    rt_in: RecurringTransactionUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTransactionOut:
    rt = crud_recurring_transaction.get_recurring(db, current_user.id, recurring_id)
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción recurrente no encontrada")
    updated = crud_recurring_transaction.update_recurring(db, rt, rt_in)
    return RecurringTransactionOut.model_validate(updated)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring(
    recurring_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> None:
    rt = crud_recurring_transaction.get_recurring(db, current_user.id, recurring_id)
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción recurrente no encontrada")
    crud_recurring_transaction.delete_recurring(db, rt)
