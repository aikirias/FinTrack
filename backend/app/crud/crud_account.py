from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


def list_accounts(db: Session, user_id: int) -> list[Account]:
    return (
        db.query(Account)
        .filter(Account.user_id == user_id)
        .order_by(Account.is_archived.asc(), Account.name.asc())
        .all()
    )


def get_account(db: Session, user_id: int, account_id: int) -> Account | None:
    return (
        db.query(Account)
        .filter(Account.user_id == user_id, Account.id == account_id)
        .first()
    )


def create_account(db: Session, user_id: int, account_in: AccountCreate, is_default: bool = False) -> Account:
    account = Account(
        user_id=user_id,
        name=account_in.name,
        currency_code=account_in.currency_code,
        description=account_in.description,
        is_default=is_default,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(db: Session, account: Account, account_in: AccountUpdate) -> Account:
    data = account_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(account, field, value)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
