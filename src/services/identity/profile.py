from fastapi import HTTPException
from sqlmodel import Session

from src.lib.security import hash_password, verify_password
from src.models.identity.user import User

_WRONG_PASSWORD = "Email or password is incorrect."


def update_profile(
    session: Session,
    user: User,
    *,
    name: str,
    title: str,
    department: str,
) -> User:
    user.name = name.strip()
    user.title = title.strip()
    user.department = department.strip()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def change_password(
    session: Session,
    user: User,
    *,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=401, detail=_WRONG_PASSWORD)
    user.password_hash = hash_password(new_password)
    session.add(user)
    session.commit()
