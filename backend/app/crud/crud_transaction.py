from datetime import datetime
from typing import Iterable

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, aliased

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionTransferCreate, TransactionUpdate
from app.services.conversion import convert_amounts
from app.schemas.exchange_rate import ExchangeRateValues


def _build_transaction_query(
    db: Session,
    user_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    category_ids: Iterable[int] | None = None,
    account_ids: Iterable[int] | None = None,
    currency_code: str | None = None,
    category_type: str | None = None,
    search: str | None = None,
):
    account_alias = aliased(Account)
    category_alias = aliased(Category)

    query = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .outerjoin(account_alias, Transaction.account_id == account_alias.id)
        .outerjoin(category_alias, Transaction.category_id == category_alias.id)
    )

    if start is not None:
        query = query.filter(Transaction.transaction_date >= start)
    if end is not None:
        query = query.filter(Transaction.transaction_date <= end)
    if category_ids:
        query = query.filter(Transaction.category_id.in_(category_ids))
    if account_ids:
        query = query.filter(Transaction.account_id.in_(account_ids))
    if currency_code:
        query = query.filter(Transaction.currency_code == currency_code)
    if category_type:
        query = query.filter(category_alias.type == category_type)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.notes.ilike(pattern),
                category_alias.name.ilike(pattern),
                account_alias.name.ilike(pattern),
            )
        )
    return query


def count_transactions(
    db: Session,
    user_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    category_ids: Iterable[int] | None = None,
    account_ids: Iterable[int] | None = None,
    currency_code: str | None = None,
    category_type: str | None = None,
    search: str | None = None,
) -> int:
    return _build_transaction_query(
        db, user_id, start, end, category_ids, account_ids, currency_code, category_type, search
    ).count()


def list_transactions(
    db: Session,
    user_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    category_ids: Iterable[int] | None = None,
    account_ids: Iterable[int] | None = None,
    currency_code: str | None = None,
    category_type: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Transaction]:
    return (
        _build_transaction_query(
            db, user_id, start, end, category_ids, account_ids, currency_code, category_type, search
        )
        .order_by(desc(Transaction.transaction_date))
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_transaction(db: Session, user_id: int, transaction_id: int) -> Transaction | None:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.id == transaction_id)
        .first()
    )


def create_transaction(
    db: Session,
    user_id: int,
    tx_in: TransactionCreate,
    rates: ExchangeRateValues,
    exchange_rate_id: int | None,
) -> Transaction:
    amount_ars, amount_usd, amount_btc = convert_amounts(
        tx_in.amount_original, tx_in.currency_code, rates, tx_in.rate_type
    )

    transaction = Transaction(
        user_id=user_id,
        account_id=tx_in.account_id,
        category_id=tx_in.category_id,
        subcategory_id=tx_in.subcategory_id,
        transaction_date=tx_in.transaction_date,
        currency_code=tx_in.currency_code,
        rate_type=tx_in.rate_type,
        amount_original=tx_in.amount_original,
        amount_ars=amount_ars,
        amount_usd=amount_usd,
        amount_btc=amount_btc,
        notes=tx_in.notes,
        exchange_rate_id=exchange_rate_id,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(
    db: Session,
    transaction: Transaction,
    tx_in: TransactionUpdate,
    rates: ExchangeRateValues | None,
    exchange_rate_id: int | None,
) -> Transaction:
    data = tx_in.model_dump(exclude_unset=True)

    if "amount_original" in data or "currency_code" in data or "rate_type" in data:
        if rates is None:
            raise ValueError("Se requieren cotizaciones para recalcular montos")

        new_amount_original = data.get("amount_original", transaction.amount_original)
        new_currency = data.get("currency_code", transaction.currency_code)
        new_rate_type = data.get("rate_type", transaction.rate_type)

        amount_ars, amount_usd, amount_btc = convert_amounts(
            new_amount_original,
            new_currency,
            rates,
            new_rate_type,
        )

        transaction.amount_original = new_amount_original
        transaction.currency_code = new_currency
        transaction.rate_type = new_rate_type
        transaction.amount_ars = amount_ars
        transaction.amount_usd = amount_usd
        transaction.amount_btc = amount_btc

    for field, value in data.items():
        setattr(transaction, field, value)

    if exchange_rate_id is not None:
        transaction.exchange_rate_id = exchange_rate_id

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def create_transfer(
    db: Session,
    user_id: int,
    tf_in: TransactionTransferCreate,
    rates: ExchangeRateValues,
    exchange_rate_id: int | None,
) -> tuple[Transaction, Transaction]:
    amount_ars, amount_usd, amount_btc = convert_amounts(
        tf_in.amount_original, tf_in.currency_code, rates, tf_in.rate_type
    )

    out_tx = Transaction(
        user_id=user_id,
        account_id=tf_in.from_account_id,
        transaction_date=tf_in.transaction_date,
        currency_code=tf_in.currency_code,
        rate_type=tf_in.rate_type,
        amount_original=tf_in.amount_original,
        amount_ars=amount_ars,
        amount_usd=amount_usd,
        amount_btc=amount_btc,
        notes=tf_in.notes,
        exchange_rate_id=exchange_rate_id,
        transfer_direction="out",
    )
    db.add(out_tx)
    db.flush()

    in_tx = Transaction(
        user_id=user_id,
        account_id=tf_in.to_account_id,
        transaction_date=tf_in.transaction_date,
        currency_code=tf_in.currency_code,
        rate_type=tf_in.rate_type,
        amount_original=tf_in.amount_original,
        amount_ars=amount_ars,
        amount_usd=amount_usd,
        amount_btc=amount_btc,
        notes=tf_in.notes,
        exchange_rate_id=exchange_rate_id,
        transfer_direction="in",
        transfer_pair_id=out_tx.id,
    )
    db.add(in_tx)
    db.commit()
    db.refresh(out_tx)
    db.refresh(in_tx)
    return out_tx, in_tx


def delete_transaction(db: Session, transaction: Transaction) -> None:
    db.delete(transaction)
    db.commit()
