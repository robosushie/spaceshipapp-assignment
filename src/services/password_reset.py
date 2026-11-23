from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlmodel import Session, select

from src.lib.config import Settings
from src.lib.security import hash_password, hash_token, new_refresh_token
from src.models import User
from src.services.auth import normalize_email
from src.services.mail import MailError, send_reset

_RESET_HOURS = 1


def request_reset(session: Session, settings: Settings, email: str) -> None:
    if not settings.resend_api_key.strip():
        raise HTTPException(
            status_code=503,
            detail="Password reset is unavailable until a Resend key is configured.",
        )
    normalized = normalize_email(email)
    user = session.exec(select(User).where(User.email == normalized)).first()
    if user is None or user.invite_token_hash is not None:
        return
    raw = new_refresh_token()
    user.password_reset_token_hash = hash_token(raw)
    user.password_reset_expires_at = datetime.now(UTC) + timedelta(hours=_RESET_HOURS)
    session.add(user)
    session.flush()
    link = f"{settings.web_origin.rstrip('/')}/reset-password?token={raw}"
    try:
        send_reset(settings, to=normalized, name=user.name or normalized, link=link)
    except MailError:
        session.rollback()
        return
    session.commit()


def reset_password(session: Session, *, token: str, password: str) -> None:
    user = session.exec(
        select(User).where(User.password_reset_token_hash == hash_token(token))
    ).first()
    expires = user.password_reset_expires_at if user is not None else None
    if user is None or expires is None or expires <= datetime.now(UTC):
        raise HTTPException(status_code=404, detail="This reset link is not valid.")
    user.password_hash = hash_password(password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    session.add(user)
    session.commit()
