"""OAuth clients and tokens.

Revision ID: 0003_oauth
Revises: 0002_webauthn
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_oauth"
down_revision: str | None = "0002_webauthn"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=False),
        sa.Column("client_secret_hash", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("redirect_uris", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column(
            "is_confidential",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_clients_client_id",
        "oauth_clients",
        ["client_id"],
        unique=True,
    )

    op.create_table(
        "oauth_access_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("scopes", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_access_tokens_token_hash",
        "oauth_access_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_oauth_access_tokens_client_id",
        "oauth_access_tokens",
        ["client_id"],
        unique=False,
    )

    op.create_table(
        "oauth_refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("scopes", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_refresh_tokens_token_hash",
        "oauth_refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_oauth_refresh_tokens_client_id",
        "oauth_refresh_tokens",
        ["client_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_oauth_refresh_tokens_client_id",
        table_name="oauth_refresh_tokens",
    )
    op.drop_index(
        "ix_oauth_refresh_tokens_token_hash",
        table_name="oauth_refresh_tokens",
    )
    op.drop_table("oauth_refresh_tokens")
    op.drop_index(
        "ix_oauth_access_tokens_client_id",
        table_name="oauth_access_tokens",
    )
    op.drop_index(
        "ix_oauth_access_tokens_token_hash",
        table_name="oauth_access_tokens",
    )
    op.drop_table("oauth_access_tokens")
    op.drop_index("ix_oauth_clients_client_id", table_name="oauth_clients")
    op.drop_table("oauth_clients")
