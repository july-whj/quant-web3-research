"""Create the initial authentication and research schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0001"
down_revision = None
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.Column("last_login_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "auth_challenges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("address", sa.String(42), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("nonce", sa.String(48), nullable=False, unique=True),
        sa.Column("message_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        *timestamps(),
    )
    op.create_index("ix_auth_challenges_address", "auth_challenges", ["address"])
    op.create_index("ix_auth_challenges_expires_at", "auth_challenges", ["expires_at"])
    op.create_table(
        "user_wallets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(42), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_user_wallets_user_id", "user_wallets", ["user_id"])
    op.create_index("ux_wallet_chain_address", "user_wallets", ["chain_id", "address"], unique=True)
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        *timestamps(),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])
    op.create_table(
        "login_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wallet_address", sa.String(42), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("ip_hash", sa.String(64)),
        *timestamps(),
    )
    op.create_index("ix_login_events_user_id", "login_events", ["user_id"])
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(12), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("artifact_path", sa.String(512)),
        *timestamps(),
    )
    op.create_index("ix_datasets_owner_id", "datasets", ["owner_id"])
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy_name", sa.String(64), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(12), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON()),
        sa.Column("artifact_path", sa.String(512)),
        sa.Column("error_message", sa.Text()),
        *timestamps(),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_backtest_runs_owner_id", "backtest_runs", ["owner_id"])
    op.create_index("ix_backtest_runs_status", "backtest_runs", ["status"])


def downgrade() -> None:
    for table in [
        "backtest_runs",
        "datasets",
        "login_events",
        "user_sessions",
        "user_wallets",
        "auth_challenges",
        "users",
    ]:
        op.drop_table(table)
