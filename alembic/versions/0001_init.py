"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-03-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("last_name", sa.String(length=128), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("trial_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_telegram_users_telegram_id"), "telegram_users", ["telegram_id"], unique=False)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("marzban_inbounds", sa.JSON(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("platform_hint", sa.String(length=32), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_profiles_code"), "profiles", ["code"], unique=False)

    op.create_table(
        "vpn_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.Integer(), nullable=False),
        sa.Column("marzban_username", sa.String(length=128), nullable=False),
        sa.Column("subscription_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("traffic_limit_gb", sa.Integer(), nullable=False),
        sa.Column("used_traffic_bytes", sa.BigInteger(), nullable=False),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_limit", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["telegram_user_id"], ["telegram_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("marzban_username"),
    )
    op.create_index(op.f("ix_vpn_accounts_marzban_username"), "vpn_accounts", ["marzban_username"], unique=False)

    op.create_table(
        "admin_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target", sa.String(length=128), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_actions_admin_telegram_id"), "admin_actions", ["admin_telegram_id"], unique=False)

    op.create_table(
        "bot_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "ip_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vpn_account_id", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["vpn_account_id"], ["vpn_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ip_history_ip_address"), "ip_history", ["ip_address"], unique=False)
    op.create_index(op.f("ix_ip_history_vpn_account_id"), "ip_history", ["vpn_account_id"], unique=False)

    op.create_table(
        "suspicious_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vpn_account_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.Column("auto_blocked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["vpn_account_id"], ["vpn_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vpn_account_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vpn_account_id"], ["vpn_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vpn_account_id", "profile_id", name="uq_user_profile_link"),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
    op.drop_table("suspicious_events")
    op.drop_index(op.f("ix_ip_history_vpn_account_id"), table_name="ip_history")
    op.drop_index(op.f("ix_ip_history_ip_address"), table_name="ip_history")
    op.drop_table("ip_history")
    op.drop_table("bot_settings")
    op.drop_index(op.f("ix_admin_actions_admin_telegram_id"), table_name="admin_actions")
    op.drop_table("admin_actions")
    op.drop_index(op.f("ix_vpn_accounts_marzban_username"), table_name="vpn_accounts")
    op.drop_table("vpn_accounts")
    op.drop_index(op.f("ix_profiles_code"), table_name="profiles")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_telegram_users_telegram_id"), table_name="telegram_users")
    op.drop_table("telegram_users")
