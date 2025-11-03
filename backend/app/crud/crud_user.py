from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        timezone=user_in.timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    if user_in.timezone is not None:
        user.timezone = user_in.timezone
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
