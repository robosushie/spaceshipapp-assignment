from pydantic import BaseModel, ConfigDict, Field

from src.enums.identity import UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    title: str
    department: str
    role: UserRole


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    title: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
