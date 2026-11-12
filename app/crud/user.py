from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def normalise_email(email: str) -> str:
    return email.strip().lower()


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalise_email(email)))


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        email=normalise_email(data.email), hashed_password=hash_password(data.password), full_name=data.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the active user for these credentials, or None. Takes similar time either way."""
    user = get_user_by_email(db, email)
    if not verify_password(password, user.hashed_password if user else None):
        return None
    if user is None or not user.is_active:
        return None
    return user


def update_full_name(db: Session, user: User, full_name: str) -> User:
    user.full_name = full_name
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, user: User, new_password: str) -> None:
    user.hashed_password = hash_password(new_password)
    db.commit()


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
