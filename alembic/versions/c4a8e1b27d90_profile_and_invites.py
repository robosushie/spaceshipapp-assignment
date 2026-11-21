"""profile name, member role, and invite tokens

Revision ID: c4a8e1b27d90
Revises: fe5e95168d2f
Create Date: 2026-11-22 02:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4a8e1b27d90"
down_revision: str | Sequence[str] | None = "fe5e95168d2f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'member'")
    op.execute("UPDATE users SET role = 'member' WHERE role::text = 'analyst'")
    op.add_column(
        "users", sa.Column("name", sa.String(length=120), nullable=False, server_default="")
    )
    op.alter_column("users", "name", server_default=None)
    op.add_column("users", sa.Column("invite_token_hash", sa.String(length=64), nullable=True))
    op.add_column(
        "users", sa.Column("invite_expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_users_invite_token_hash", "users", ["invite_token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_invite_token_hash", table_name="users")
    op.drop_column("users", "invite_expires_at")
    op.drop_column("users", "invite_token_hash")
    op.drop_column("users", "name")
