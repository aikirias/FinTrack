from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, aliased

from app.api import deps
from app.crud import crud_account
from app.db.session import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.account import AccountCreate, AccountOut, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=list[AccountOut])
def list_accounts(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> list[AccountOut]:
    accounts = crud_account.list_accounts(db, current_user.id)
    return [AccountOut.model_validate(acc) for acc in accounts]


# NOTE: must be before /{account_id} to avoid routing conflict
@router.get("/balances")
def get_account_balances(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    cat = aliased(Category)

    sign = case(
        (or_(cat.type == "income", Transaction.transfer_direction == "in"), 1),
        (or_(cat.type == "expense", Transaction.transfer_direction == "out"), -1),
        else_=0,
    )

    rows = (
        db.query(
            Transaction.account_id,
            func.sum(sign * Transaction.amount_ars).label("balance_ars"),
            func.sum(sign * Transaction.amount_usd).label("balance_usd"),
            func.sum(sign * Transaction.amount_btc).label("balance_btc"),
        )
        .outerjoin(cat, Transaction.category_id == cat.id)
        .filter(Transaction.user_id == current_user.id)
        .group_by(Transaction.account_id)
        .all()
    )

    return [
        {
            "account_id": row.account_id,
            "balance_ars": float(row.balance_ars or 0),
            "balance_usd": float(row.balance_usd or 0),
            "balance_btc": float(row.balance_btc or 0),
        }
        for row in rows
    ]


@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    account_in: AccountCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> AccountOut:
    account = crud_account.create_account(db, current_user.id, account_in)
    return AccountOut.model_validate(account)


@router.patch("/{account_id}", response_model=AccountOut)
def update_account(
    account_id: int,
    account_in: AccountUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> AccountOut:
    account = crud_account.get_account(db, current_user.id, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    updated = crud_account.update_account(db, account, account_in)
    return AccountOut.model_validate(updated)
