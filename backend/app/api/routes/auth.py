from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services.defaults import seed_defaults_for_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str, expires_minutes: int) -> None:
    max_age = expires_minutes * 60
    expires = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)
    cookie_kwargs: dict[str, Any] = {
        "key": "access_token",
        "value": token,
        "max_age": max_age,
        "expires": expires,
        "httponly": True,
        "samesite": "lax",
        "secure": settings.app_env == "production",
    }
    if settings.cookie_domain:
        cookie_kwargs["domain"] = settings.cookie_domain
    response.set_cookie(**cookie_kwargs)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(response: Response, user_in: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing = crud_user.get_by_email(db, user_in.email.lower())
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")

    user = crud_user.create_user(db, user_in)
    seed_defaults_for_user(db, user.id)
    token = create_access_token(user.email)
    _set_auth_cookie(response, token, settings.access_token_expire_minutes)
    return UserOut.model_validate(user)


@router.post("/login", response_model=UserOut)
def login(response: Response, credentials: UserLogin, db: Session = Depends(get_db)) -> UserOut:
    user = deps.authenticate_user(db, credentials)
    token = create_access_token(user.email)
    _set_auth_cookie(response, token, settings.access_token_expire_minutes)
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie("access_token")


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(deps.get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
