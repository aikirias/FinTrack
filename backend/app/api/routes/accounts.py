from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_account
from app.db.session import get_db
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
