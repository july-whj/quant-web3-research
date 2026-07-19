"""Add immutable strategy configurations and link them to backtests."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0004"
down_revision = "20260719_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "strategy_configs" not in tables:
        op.create_table(
            "strategy_configs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "owner_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("latest_version_number", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_strategy_configs_owner_id", "strategy_configs", ["owner_id"])

    inspector = sa.inspect(bind)
    if "strategy_config_versions" not in set(inspector.get_table_names()):
        op.create_table(
            "strategy_config_versions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "config_id",
                sa.String(36),
                sa.ForeignKey("strategy_configs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("strategy_name", sa.String(64), nullable=False),
            sa.Column("strategy_version", sa.String(32), nullable=False),
            sa.Column("exchange", sa.String(32), nullable=False),
            sa.Column("symbol", sa.String(32), nullable=False),
            sa.Column("timeframe", sa.String(12), nullable=False),
            sa.Column("days", sa.Integer(), nullable=False),
            sa.Column("parameters", sa.JSON(), nullable=False),
            sa.Column("risk_config", sa.JSON(), nullable=False),
            sa.Column("execution_config", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint(
                "config_id",
                "version_number",
                name="ux_strategy_config_version_number",
            ),
        )
        op.create_index(
            "ix_strategy_config_versions_config_id",
            "strategy_config_versions",
            ["config_id"],
        )

    inspector = sa.inspect(bind)
    backtest_columns = {
        column["name"] for column in inspector.get_columns("backtest_runs")
    }
    if "strategy_config_version_id" not in backtest_columns:
        op.add_column(
            "backtest_runs",
            sa.Column("strategy_config_version_id", sa.String(36)),
        )
    if "risk_config" not in backtest_columns:
        op.add_column("backtest_runs", sa.Column("risk_config", sa.JSON(), nullable=True))

    inspector = sa.inspect(bind)
    backtest_foreign_keys = {
        foreign_key["name"] for foreign_key in inspector.get_foreign_keys("backtest_runs")
    }
    if "fk_backtest_runs_strategy_config_version" not in backtest_foreign_keys:
        op.create_foreign_key(
            "fk_backtest_runs_strategy_config_version",
            "backtest_runs",
            "strategy_config_versions",
            ["strategy_config_version_id"],
            ["id"],
            ondelete="SET NULL",
        )
    inspector = sa.inspect(bind)
    backtest_indexes = {
        index["name"] for index in inspector.get_indexes("backtest_runs")
    }
    if "ix_backtest_runs_strategy_config_version_id" not in backtest_indexes:
        op.create_index(
            "ix_backtest_runs_strategy_config_version_id",
            "backtest_runs",
            ["strategy_config_version_id"],
        )


def downgrade() -> None:
    op.drop_column("backtest_runs", "risk_config")
    op.drop_index("ix_backtest_runs_strategy_config_version_id", table_name="backtest_runs")
    op.drop_constraint(
        "fk_backtest_runs_strategy_config_version",
        "backtest_runs",
        type_="foreignkey",
    )
    op.drop_column("backtest_runs", "strategy_config_version_id")
    op.drop_index(
        "ix_strategy_config_versions_config_id",
        table_name="strategy_config_versions",
    )
    op.drop_table("strategy_config_versions")
    op.drop_index("ix_strategy_configs_owner_id", table_name="strategy_configs")
    op.drop_table("strategy_configs")
