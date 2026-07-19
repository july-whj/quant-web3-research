from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


def uuid_string() -> str:
    return str(uuid.uuid4())


class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    exchange: Mapped[str] = mapped_column(String(32), default="binance", nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), default="BTC/USDT", nullable=False)
    base_currency: Mapped[str] = mapped_column(String(16), default="USDT", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True, nullable=False)
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(12, 10), default=Decimal("0.001"))
    slippage_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 10), default=Decimal("0.0005")
    )
    max_position_pct: Mapped[Decimal] = mapped_column(Numeric(8, 6), default=Decimal("1"))
    max_order_notional: Mapped[Decimal] = mapped_column(
        Numeric(30, 12), default=Decimal("1000000")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PaperBalance(Base):
    __tablename__ = "paper_balances"
    __table_args__ = (UniqueConstraint("account_id", "asset", name="ux_paper_balance_asset"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    asset: Mapped[str] = mapped_column(String(16), nullable=False)
    available: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    locked: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PaperLedgerEntry(Base):
    __tablename__ = "paper_ledger_entries"
    __table_args__ = (Index("ix_paper_ledger_account_time", "account_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    asset: Mapped[str] = mapped_column(String(16), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    available_after: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    locked_after: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(32))
    reference_id: Mapped[str | None] = mapped_column(String(36), index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaperBot(Base):
    __tablename__ = "paper_bots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    bot_type: Mapped[str] = mapped_column(String(32), default="spot_grid", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    lower_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    upper_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    grid_count: Mapped[int] = mapped_column(Integer, nullable=False)
    grid_mode: Mapped[str] = mapped_column(String(20), default="arithmetic", nullable=False)
    investment: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    realized_profit: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    last_processed_market_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PaperOrder(Base):
    __tablename__ = "paper_orders"
    __table_args__ = (
        UniqueConstraint("account_id", "client_order_id", name="ux_paper_client_order"),
        Index("ix_paper_orders_match", "status", "exchange", "symbol", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    bot_id: Mapped[str | None] = mapped_column(
        ForeignKey("paper_bots.id", ondelete="SET NULL"), index=True
    )
    client_order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    filled_quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    average_price: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    reserved_asset: Mapped[str | None] = mapped_column(String(16))
    reserved_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    slippage_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    gas_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    grid_level: Mapped[int | None] = mapped_column(Integer)
    paired_level: Mapped[int | None] = mapped_column(Integer)
    rejection_reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaperFill(Base):
    __tablename__ = "paper_fills"
    __table_args__ = (Index("ix_paper_fills_account_time", "account_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("paper_orders.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    reference_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    execution_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    quote_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    slippage_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    gas_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    market_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cost_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaperPosition(Base):
    __tablename__ = "paper_positions"
    __table_args__ = (UniqueConstraint("account_id", "symbol", name="ux_paper_position_symbol"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(30, 12), default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PaperRiskEvent(Base):
    __tablename__ = "paper_risk_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("paper_orders.id", ondelete="SET NULL"), index=True
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaperBotEvent(Base):
    __tablename__ = "paper_bot_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    bot_id: Mapped[str] = mapped_column(
        ForeignKey("paper_bots.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaperAccountSnapshot(Base):
    __tablename__ = "paper_account_snapshots"
    __table_args__ = (Index("ix_paper_snapshot_account_time", "account_id", "market_time"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    market_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quote_balance: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    base_quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    mark_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
