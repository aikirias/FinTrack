import csv
import io
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_account, crud_category, crud_transaction
from app.db.session import get_db
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.exchange_rate import ExchangeRateOverride
from app.schemas.transaction import TransactionCreate, TransactionOut, TransactionTransferCreate, TransactionUpdate
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
    response: Response,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    category_ids: List[int] | None = Query(default=None),
    account_ids: List[int] | None = Query(default=None),
    currency_code: str | None = Query(default=None, min_length=3, max_length=3),
    category_type: CategoryType | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[TransactionOut]:
    normalized_currency = currency_code.upper() if currency_code else None
    normalized_search = search.strip() if search else None
    filter_kwargs = dict(
        user_id=current_user.id,
        start=start,
        end=end,
        category_ids=category_ids,
        account_ids=account_ids,
        currency_code=normalized_currency,
        category_type=category_type.value if category_type else None,
        search=normalized_search,
    )
    total = crud_transaction.count_transactions(db, **filter_kwargs)
    items = crud_transaction.list_transactions(db, **filter_kwargs, limit=limit, offset=offset)
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
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


# NOTE: must be defined before /{transaction_id} to avoid routing conflicts
@router.post("/transfer", response_model=List[TransactionOut], status_code=status.HTTP_201_CREATED)
def create_transfer(
    tf_in: TransactionTransferCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> List[TransactionOut]:
    if tf_in.from_account_id == tf_in.to_account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Las cuentas origen y destino deben ser distintas")
    from_account = crud_account.get_account(db, current_user.id, tf_in.from_account_id)
    if not from_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta origen no encontrada")
    to_account = crud_account.get_account(db, current_user.id, tf_in.to_account_id)
    if not to_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta destino no encontrada")

    exchange_rate_obj, rate_values = exchange_rates.pick_rates(
        db_session=db,
        exchange_rate_id=tf_in.exchange_rate_id,
        manual_rates=tf_in.manual_rates,
    )
    out_tx, in_tx = crud_transaction.create_transfer(
        db,
        user_id=current_user.id,
        tf_in=tf_in,
        rates=rate_values,
        exchange_rate_id=exchange_rate_obj.id if exchange_rate_obj else None,
    )
    return [TransactionOut.model_validate(out_tx), TransactionOut.model_validate(in_tx)]


# NOTE: this route must be defined before /{transaction_id} to avoid routing conflicts
@router.get("/export/csv")
def export_transactions_csv(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    account_ids: List[int] | None = Query(default=None),
    category_ids: List[int] | None = Query(default=None),
    currency_code: str | None = Query(default=None, min_length=3, max_length=3),
    category_type: CategoryType | None = Query(default=None),
    search: str | None = Query(default=None),
) -> StreamingResponse:
    items = crud_transaction.list_transactions(
        db,
        user_id=current_user.id,
        start=start,
        end=end,
        category_ids=category_ids,
        account_ids=account_ids,
        currency_code=currency_code.upper() if currency_code else None,
        category_type=category_type.value if category_type else None,
        search=search.strip() if search else None,
        limit=10_000,
        offset=0,
    )

    def _csv_safe(value: object) -> str:
        """Escape CSV injection: prefix formula-starting characters with a tab."""
        s = str(value) if value is not None else ""
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "\t" + s
        return s

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "fecha", "cuenta", "moneda", "monto_original",
        "monto_ars", "monto_usd", "monto_btc",
        "categoria_id", "subcategoria_id", "tipo_tasa", "notas",
    ])
    for tx in items:
        account_name = tx.account.name if tx.account else (tx.account_id or "")
        writer.writerow([
            tx.id,
            tx.transaction_date.isoformat(),
            _csv_safe(account_name),
            tx.currency_code,
            tx.amount_original,
            tx.amount_ars,
            tx.amount_usd,
            tx.amount_btc,
            tx.category_id if tx.category_id is not None else "",
            tx.subcategory_id if tx.subcategory_id is not None else "",
            tx.rate_type,
            _csv_safe(tx.notes or ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=movimientos.csv"},
    )


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
            exchange_rate_id=tx_in.exchange_rate_id or transaction.exchange_rate_id,
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
