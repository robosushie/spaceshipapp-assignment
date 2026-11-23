from fastapi import APIRouter, HTTPException, Request, Response

from src.api.deps import SessionDep, SettingsDep
from src.lib.rate_limit import login_limiter
from src.schemas import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
)
from src.services.auth import (
    authenticate,
    issue_tokens,
    revoke_refresh,
    rotate_refresh,
    set_refresh_cookie,
)
from src.services.password_reset import request_reset, reset_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_host(request: Request) -> str:
    if request.client is None:
        return "unknown"
    return request.client.host


@router.post("/login", response_model=AccessTokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> AccessTokenResponse:
    retry_after = login_limiter.retry_after(_client_host(request))
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )
    user = authenticate(session, body.email, body.password)
    token, raw = issue_tokens(session, user, settings)
    set_refresh_cookie(response, raw, settings)
    return token


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> AccessTokenResponse:
    token, raw = rotate_refresh(session, request.cookies.get("refresh_token"), settings)
    set_refresh_cookie(response, raw, settings)
    return token


@router.post("/forgot", status_code=204)
def forgot(body: ForgotPasswordRequest, session: SessionDep, settings: SettingsDep) -> None:
    request_reset(session, settings, body.email)


@router.post("/reset", status_code=204)
def reset(body: ResetPasswordRequest, session: SessionDep) -> None:
    reset_password(session, token=body.token, password=body.password)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, session: SessionDep) -> Response:
    revoke_refresh(session, request.cookies.get("refresh_token"))
    response.delete_cookie("refresh_token", path="/v1/auth")
    response.status_code = 204
    return response
