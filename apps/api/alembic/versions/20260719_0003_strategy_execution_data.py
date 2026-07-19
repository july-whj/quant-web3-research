"""Separate strategy, execution, and market-data snapshots for backtests."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0003"
down_revision = "20260719_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "backtest_runs",
        sa.Column("strategy_version", sa.String(32), nullable=False, server_default="1.0.0"),
    )
    op.add_column(
        "backtest_runs",
        sa.Column("exchange", sa.String(32), nullable=False, server_default="binance"),
    )
    # Nullable JSON columns preserve backtests created before the execution/data
    # split. Every newly created run writes both fields.
    op.add_column("backtest_runs", sa.Column("execution_config", sa.JSON(), nullable=True))
    op.add_column("backtest_runs", sa.Column("data_snapshot", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("backtest_runs", "data_snapshot")
    op.drop_column("backtest_runs", "execution_config")
    op.drop_column("backtest_runs", "exchange")
    op.drop_column("backtest_runs", "strategy_version")
