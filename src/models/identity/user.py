from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from src.enums.identity import UserRole
from src.models.columns import enum_values


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String(320), unique=True, nullable=False))
    name: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)
    password_hash: str
    role: UserRole = Field(
        sa_column=Column(
            SAEnum(UserRole, name="user_role", values_callable=enum_values),
            nullable=False,
        )
    )
    invite_token_hash: str | None = Field(default=None, max_length=64, unique=True)
    invite_expires_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    password_reset_token_hash: str | None = Field(default=None, max_length=64, unique=True)
    password_reset_expires_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
