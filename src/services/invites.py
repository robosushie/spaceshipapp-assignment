from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlmodel import Session, select

from src.enums import UserRole
from src.lib.config import Settings
from src.lib.security import hash_password, hash_token, new_refresh_token
from src.models import User
from src.services.auth import normalize_email
from src.services.mail import MailError, send_invite

_INVITE_DAYS = 7


def create_invite(
    session: Session,
    settings: Settings,
    *,
    name: str,
    email: str,
    role: UserRole,
    title: str = "",
    department: str = "",
) -> str:
    normalized = normalize_email(email)
    existing = session.exec(select(User).where(User.email == normalized)).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="That email already has an account.")
    raw = new_refresh_token()
    user = User(
        email=normalized,
        name=name.strip(),
        title=title.strip(),
        department=department.strip(),
        password_hash=hash_password(new_refresh_token()),
        role=role,
        invite_token_hash=hash_token(raw),
        invite_expires_at=datetime.now(UTC) + timedelta(days=_INVITE_DAYS),
    )
    session.add(user)
    session.flush()
    link = f"{settings.web_origin.rstrip('/')}/accept-invite?token={raw}"
    try:
        send_invite(settings, to=normalized, name=user.name, link=link)
    except MailError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="The invite email could not be sent.") from exc
    session.commit()
    return normalized


def accept_invite(session: Session, *, token: str, password: str) -> None:
    user = session.exec(select(User).where(User.invite_token_hash == hash_token(token))).first()
    expires = user.invite_expires_at if user is not None else None
    if user is None or expires is None or expires <= datetime.now(UTC):
        raise HTTPException(status_code=404, detail="This invite link is not valid.")
    user.password_hash = hash_password(password)
    user.invite_token_hash = None
    user.invite_expires_at = None
    session.add(user)
    session.commit()
