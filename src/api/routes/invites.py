from fastapi import APIRouter, HTTPException

from src.api.deps import CurrentUser, SessionDep, SettingsDep
from src.enums import UserRole
from src.schemas import AcceptInviteRequest, InviteRequest
from src.services.invites import accept_invite, create_invite

router = APIRouter(prefix="/invites", tags=["invites"])


@router.post("", status_code=201)
def create(
    body: InviteRequest,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> dict[str, str]:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only an admin can invite.")
    email = create_invite(
        session,
        settings,
        name=body.name,
        email=body.email,
        role=body.role,
        title=body.title,
        department=body.department,
    )
    return {"email": email}


@router.post("/accept", status_code=204)
def accept(body: AcceptInviteRequest, session: SessionDep) -> None:
    accept_invite(session, token=body.token, password=body.password)
