from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(deps.get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut)
def update_user_me(
    payload: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    user = crud_user.get_user(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    updated = crud_user.update_user(db, user, payload)
    return UserOut.model_validate(updated)
