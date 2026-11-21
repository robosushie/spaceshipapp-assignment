from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from src.lib.config import Settings, get_settings
from src.lib.db import get_session
from src.lib.security import decode_access_token
from src.models import User

bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        payload = decode_access_token(credentials.credentials, settings)
        user_id = int(payload["sub"])
    except jwt.PyJWTError, ValueError, TypeError:
        raise HTTPException(status_code=401, detail="Authentication required.") from None
    user = session.get(User, user_id)
    if user is None or user.id is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
