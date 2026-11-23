"""title, department, and password reset tokens

Revision ID: d8f2a6c41b07
Revises: c4a8e1b27d90
Create Date: 2026-11-22 03:19:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8f2a6c41b07"
down_revision: str | Sequence[str] | None = "c4a8e1b27d90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("title", sa.String(length=120), nullable=False, server_default="")
    )
    op.add_column(
        "users", sa.Column("department", sa.String(length=120), nullable=False, server_default="")
    )
    op.alter_column("users", "title", server_default=None)
    op.alter_column("users", "department", server_default=None)
    op.add_column(
        "users", sa.Column("password_reset_token_hash", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_password_reset_token_hash",
        "users",
        ["password_reset_token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_password_reset_token_hash", table_name="users")
    op.drop_column("users", "password_reset_expires_at")
    op.drop_column("users", "password_reset_token_hash")
    op.drop_column("users", "department")
    op.drop_column("users", "title")
