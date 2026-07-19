"""Add durable market candles and ingestion checkpoints."""

from alembic import op
import sqlalchemy as sa


revision = "20260719_0002"
down_revision = "20260719_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_candles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(12), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(30, 12), nullable=False),
        sa.Column("high", sa.Numeric(30, 12), nullable=False),
        sa.Column("low", sa.Numeric(30, 12), nullable=False),
        sa.Column("close", sa.Numeric(30, 12), nullable=False),
        sa.Column("volume", sa.Numeric(38, 18), nullable=False),
        sa.Column("trade_count", sa.Integer()),
        sa.Column("is_closed", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("source_event_time", sa.DateTime(timezone=True)),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "exchange",
            "symbol",
            "timeframe",
            "open_time",
            name="ux_market_candle_identity",
        ),
    )
    op.create_index(
        "ix_market_candles_stream_time",
        "market_candles",
        ["exchange", "symbol", "timeframe", "open_time"],
    )
    op.create_table(
        "ingestion_checkpoints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(12), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("last_closed_open_time", sa.DateTime(timezone=True)),
        sa.Column("last_event_time", sa.DateTime(timezone=True)),
        sa.Column("last_received_at", sa.DateTime(timezone=True)),
        sa.Column("last_persisted_at", sa.DateTime(timezone=True)),
        sa.Column("last_backfill_at", sa.DateTime(timezone=True)),
        sa.Column("reconnect_count", sa.Integer(), nullable=False),
        sa.Column("backfilled_candles", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "exchange",
            "symbol",
            "timeframe",
            name="ux_ingestion_checkpoint_stream",
        ),
    )


def downgrade() -> None:
    op.drop_table("ingestion_checkpoints")
    op.drop_index("ix_market_candles_stream_time", table_name="market_candles")
    op.drop_table("market_candles")
