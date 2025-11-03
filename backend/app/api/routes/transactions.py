from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_account, crud_category, crud_transaction
from app.db.session import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.exchange_rate import ExchangeRateOverride
from app.schemas.transaction import TransactionCreate, TransactionOut, TransactionUpdate
from app.services import exchange_rates

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _validate_category(
    db: Session,
    user_id: int,
    category_id: int | None,
    subcategory_id: int | None,
) -> None:
    if category_id is None and subcategory_id is None:
        return

    category: Category | None = None
    subcategory: Category | None = None

    if category_id is not None:
        category = crud_category.get_category(db, user_id, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    if subcategory_id is not None:
        subcategory = crud_category.get_category(db, user_id, subcategory_id)
        if not subcategory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoría no encontrada")
        if subcategory.parent_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La subcategoría debe tener padre")

    if subcategory and category and subcategory.parent_id != category.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La subcategoría no pertenece a la categoría indicada")

    if subcategory and category is None:
        parent = crud_category.get_category(db, user_id, subcategory.parent_id)
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La subcategoría no tiene categoría padre válida")


@router.get("/", response_model=List[TransactionOut])
def list_transactions(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    category_ids: List[int] | None = Query(default=None),
    account_ids: List[int] | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[TransactionOut]:
    items = crud_transaction.list_transactions(
        db,
        user_id=current_user.id,
        start=start,
        end=end,
        category_ids=category_ids,
        account_ids=account_ids,
        limit=limit,
        offset=offset,
    )
    return [TransactionOut.model_validate(item) for item in items]


@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> TransactionOut:
    account = crud_account.get_account(db, current_user.id, tx_in.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    _validate_category(db, current_user.id, tx_in.category_id, tx_in.subcategory_id)

    exchange_rate_obj, rate_values = exchange_rates.pick_rates(
        db_session=db,
        exchange_rate_id=tx_in.exchange_rate_id,
        manual_rates=tx_in.manual_rates,
    )
    exchange_rate_id = exchange_rate_obj.id if exchange_rate_obj else None

    transaction = crud_transaction.create_transaction(
        db,
        user_id=current_user.id,
        tx_in=tx_in,
        rates=rate_values,
        exchange_rate_id=exchange_rate_id,
    )
    if tx_in.manual_rates:
        transaction.exchange_rate = exchange_rate_obj
    return TransactionOut.model_validate(transaction)


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> TransactionOut:
    transaction = crud_transaction.get_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado")
    return TransactionOut.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int,
    tx_in: TransactionUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> TransactionOut:
    transaction = crud_transaction.get_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado")

    if tx_in.account_id is not None:
        account = crud_account.get_account(db, current_user.id, tx_in.account_id)
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    _validate_category(
        db,
        current_user.id,
        tx_in.category_id or transaction.category_id,
        tx_in.subcategory_id or transaction.subcategory_id,
    )

    exchange_rate_obj = None
    rate_values = None
    if any(
        [
            tx_in.manual_rates is not None,
            tx_in.exchange_rate_id is not None,
            tx_in.amount_original is not None,
            tx_in.currency_code is not None,
            tx_in.rate_type is not None,
        ]
    ):
        exchange_rate_obj, rate_values = exchange_rates.pick_rates(
            db_session=db,
            exchange_rate_id=tx_in.exchange_rate_id,
            manual_rates=tx_in.manual_rates,
        )

    updated = crud_transaction.update_transaction(
        db,
        transaction=transaction,
        tx_in=tx_in,
        rates=rate_values,
        exchange_rate_id=exchange_rate_obj.id if exchange_rate_obj else None,
    )
    if isinstance(tx_in.manual_rates, ExchangeRateOverride):
        updated.exchange_rate = exchange_rate_obj
    return TransactionOut.model_validate(updated)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> None:
    transaction = crud_transaction.get_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado")
    crud_transaction.delete_transaction(db, transaction)
