from fastapi import APIRouter

from src.api.deps import CurrentUser, SessionDep
from src.schemas import PasswordChange, ProfileUpdate, UserPublic
from src.services.profile import change_password, update_profile

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserPublic)
def read_me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


@router.post("", response_model=UserPublic)
def write_me(body: ProfileUpdate, user: CurrentUser, session: SessionDep) -> UserPublic:
    updated = update_profile(
        session,
        user,
        name=body.name,
        title=body.title,
        department=body.department,
    )
    return UserPublic.model_validate(updated)


@router.post("/password", status_code=204)
def write_password(body: PasswordChange, user: CurrentUser, session: SessionDep) -> None:
    change_password(
        session,
        user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
