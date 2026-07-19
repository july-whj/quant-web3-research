"""Add paper-funds accounts, orders, ledger, positions and grid bots."""

from alembic import op
import sqlalchemy as sa


revision = "20260720_0005"
down_revision = "20260719_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "paper_accounts" not in existing:
        op.create_table(
            "paper_accounts",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("exchange", sa.String(32), nullable=False),
            sa.Column("symbol", sa.String(32), nullable=False),
            sa.Column("base_currency", sa.String(16), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("fee_rate", sa.Numeric(12, 10), nullable=False),
            sa.Column("slippage_rate", sa.Numeric(12, 10), nullable=False),
            sa.Column("max_position_pct", sa.Numeric(8, 6), nullable=False),
            sa.Column("max_order_notional", sa.Numeric(30, 12), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_paper_accounts_owner_id", "paper_accounts", ["owner_id"])
        op.create_index("ix_paper_accounts_status", "paper_accounts", ["status"])
    if "paper_balances" not in existing:
        op.create_table(
            "paper_balances",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("asset", sa.String(16), nullable=False),
            sa.Column("available", sa.Numeric(30, 12), nullable=False),
            sa.Column("locked", sa.Numeric(30, 12), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("account_id", "asset", name="ux_paper_balance_asset"),
        )
        op.create_index("ix_paper_balances_account_id", "paper_balances", ["account_id"])
    if "paper_bots" not in existing:
        op.create_table(
            "paper_bots",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("bot_type", sa.String(32), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("lower_price", sa.Numeric(30, 12), nullable=False),
            sa.Column("upper_price", sa.Numeric(30, 12), nullable=False),
            sa.Column("grid_count", sa.Integer(), nullable=False),
            sa.Column("grid_mode", sa.String(20), nullable=False),
            sa.Column("investment", sa.Numeric(30, 12), nullable=False),
            sa.Column("parameters", sa.JSON(), nullable=False),
            sa.Column("realized_profit", sa.Numeric(30, 12), nullable=False),
            sa.Column("last_processed_market_time", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("stopped_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_paper_bots_account_id", "paper_bots", ["account_id"])
        op.create_index("ix_paper_bots_status", "paper_bots", ["status"])
    if "paper_orders" not in existing:
        op.create_table(
            "paper_orders",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("bot_id", sa.String(36), sa.ForeignKey("paper_bots.id", ondelete="SET NULL")),
            sa.Column("client_order_id", sa.String(64), nullable=False),
            sa.Column("exchange", sa.String(32), nullable=False),
            sa.Column("symbol", sa.String(32), nullable=False),
            sa.Column("side", sa.String(8), nullable=False),
            sa.Column("order_type", sa.String(16), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("quantity", sa.Numeric(30, 12), nullable=False),
            sa.Column("limit_price", sa.Numeric(30, 12)),
            sa.Column("filled_quantity", sa.Numeric(30, 12), nullable=False),
            sa.Column("average_price", sa.Numeric(30, 12)),
            sa.Column("reserved_asset", sa.String(16)),
            sa.Column("reserved_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("fee_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("slippage_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("gas_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("grid_level", sa.Integer()),
            sa.Column("paired_level", sa.Integer()),
            sa.Column("rejection_reason", sa.String(255)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("filled_at", sa.DateTime(timezone=True)),
            sa.Column("cancelled_at", sa.DateTime(timezone=True)),
            sa.UniqueConstraint("account_id", "client_order_id", name="ux_paper_client_order"),
        )
        op.create_index("ix_paper_orders_account_id", "paper_orders", ["account_id"])
        op.create_index("ix_paper_orders_bot_id", "paper_orders", ["bot_id"])
        op.create_index("ix_paper_orders_status", "paper_orders", ["status"])
        op.create_index("ix_paper_orders_match", "paper_orders", ["status", "exchange", "symbol", "created_at"])
    if "paper_ledger_entries" not in existing:
        op.create_table(
            "paper_ledger_entries",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("asset", sa.String(16), nullable=False),
            sa.Column("entry_type", sa.String(32), nullable=False),
            sa.Column("amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("available_after", sa.Numeric(30, 12), nullable=False),
            sa.Column("locked_after", sa.Numeric(30, 12), nullable=False),
            sa.Column("reference_type", sa.String(32)),
            sa.Column("reference_id", sa.String(36)),
            sa.Column("description", sa.String(255)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_paper_ledger_entries_account_id", "paper_ledger_entries", ["account_id"])
        op.create_index("ix_paper_ledger_entries_reference_id", "paper_ledger_entries", ["reference_id"])
        op.create_index("ix_paper_ledger_account_time", "paper_ledger_entries", ["account_id", "created_at"])
    if "paper_fills" not in existing:
        op.create_table(
            "paper_fills",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("order_id", sa.String(36), sa.ForeignKey("paper_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("side", sa.String(8), nullable=False),
            sa.Column("reference_price", sa.Numeric(30, 12), nullable=False),
            sa.Column("execution_price", sa.Numeric(30, 12), nullable=False),
            sa.Column("quantity", sa.Numeric(30, 12), nullable=False),
            sa.Column("quote_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("fee_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("slippage_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("gas_amount", sa.Numeric(30, 12), nullable=False),
            sa.Column("market_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("cost_snapshot", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_paper_fills_order_id", "paper_fills", ["order_id"])
        op.create_index("ix_paper_fills_account_id", "paper_fills", ["account_id"])
        op.create_index("ix_paper_fills_account_time", "paper_fills", ["account_id", "created_at"])
    if "paper_positions" not in existing:
        op.create_table(
            "paper_positions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("symbol", sa.String(32), nullable=False),
            sa.Column("quantity", sa.Numeric(30, 12), nullable=False),
            sa.Column("average_cost", sa.Numeric(30, 12), nullable=False),
            sa.Column("realized_pnl", sa.Numeric(30, 12), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("account_id", "symbol", name="ux_paper_position_symbol"),
        )
        op.create_index("ix_paper_positions_account_id", "paper_positions", ["account_id"])
    if "paper_risk_events" not in existing:
        op.create_table(
            "paper_risk_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.String(36), sa.ForeignKey("paper_orders.id", ondelete="SET NULL")),
            sa.Column("decision", sa.String(16), nullable=False),
            sa.Column("code", sa.String(40), nullable=False),
            sa.Column("reason", sa.String(255), nullable=False),
            sa.Column("snapshot", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_paper_risk_events_account_id", "paper_risk_events", ["account_id"])
        op.create_index("ix_paper_risk_events_order_id", "paper_risk_events", ["order_id"])
    if "paper_bot_events" not in existing:
        op.create_table(
            "paper_bot_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("bot_id", sa.String(36), sa.ForeignKey("paper_bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(32), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_paper_bot_events_bot_id", "paper_bot_events", ["bot_id"])
    if "paper_account_snapshots" not in existing:
        op.create_table(
            "paper_account_snapshots",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("market_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("quote_balance", sa.Numeric(30, 12), nullable=False),
            sa.Column("base_quantity", sa.Numeric(30, 12), nullable=False),
            sa.Column("mark_price", sa.Numeric(30, 12), nullable=False),
            sa.Column("equity", sa.Numeric(30, 12), nullable=False),
            sa.Column("realized_pnl", sa.Numeric(30, 12), nullable=False),
            sa.Column("unrealized_pnl", sa.Numeric(30, 12), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_paper_account_snapshots_account_id", "paper_account_snapshots", ["account_id"])
        op.create_index("ix_paper_snapshot_account_time", "paper_account_snapshots", ["account_id", "market_time"])


def downgrade() -> None:
    for table in [
        "paper_account_snapshots",
        "paper_bot_events",
        "paper_risk_events",
        "paper_positions",
        "paper_fills",
        "paper_ledger_entries",
        "paper_orders",
        "paper_bots",
        "paper_balances",
        "paper_accounts",
    ]:
        op.drop_table(table)
