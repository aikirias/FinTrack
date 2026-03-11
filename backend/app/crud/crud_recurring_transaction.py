from datetime import date

from sqlalchemy.orm import Session

from app.models.recurring_transaction import RecurringTransaction
from app.schemas.recurring_transaction import RecurringTransactionCreate, RecurringTransactionUpdate


def list_recurring(db: Session, user_id: int) -> list[RecurringTransaction]:
    return (
        db.query(RecurringTransaction)
        .filter(RecurringTransaction.user_id == user_id)
        .order_by(RecurringTransaction.created_at.desc())
        .all()
    )


def get_recurring(db: Session, user_id: int, recurring_id: int) -> RecurringTransaction | None:
    return (
        db.query(RecurringTransaction)
        .filter(RecurringTransaction.user_id == user_id, RecurringTransaction.id == recurring_id)
        .first()
    )


def get_due(db: Session, as_of: date) -> list[RecurringTransaction]:
    """Return all active recurring transactions due on or before as_of."""
    return (
        db.query(RecurringTransaction)
        .filter(
            RecurringTransaction.is_active == True,  # noqa: E712
            RecurringTransaction.next_run_date <= as_of,
        )
        .all()
    )


def create_recurring(
    db: Session,
    user_id: int,
    rt_in: RecurringTransactionCreate,
) -> RecurringTransaction:
    rt = RecurringTransaction(
        user_id=user_id,
        account_id=rt_in.account_id,
        category_id=rt_in.category_id,
        subcategory_id=rt_in.subcategory_id,
        name=rt_in.name,
        amount_original=rt_in.amount_original,
        currency_code=rt_in.currency_code,
        rate_type=rt_in.rate_type,
        notes=rt_in.notes,
        frequency=rt_in.frequency,
        next_run_date=rt_in.next_run_date,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def update_recurring(
    db: Session,
    rt: RecurringTransaction,
    rt_in: RecurringTransactionUpdate,
) -> RecurringTransaction:
    for field, value in rt_in.model_dump(exclude_unset=True).items():
        setattr(rt, field, value)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def delete_recurring(db: Session, rt: RecurringTransaction) -> None:
    db.delete(rt)
    db.commit()
