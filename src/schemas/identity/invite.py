from pydantic import BaseModel, Field

from src.enums.identity import UserRole


class InviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    role: UserRole
    title: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=8, max_length=200)
