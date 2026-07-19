from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


def uuid_string() -> str:
    return str(uuid.uuid4())


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(12), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarketCandle(Base):
    """A finalized exchange candle used as the durable hot-data layer."""

    __tablename__ = "market_candles"
    __table_args__ = (
        UniqueConstraint(
            "exchange",
            "symbol",
            "timeframe",
            "open_time",
            name="ux_market_candle_identity",
        ),
        Index(
            "ix_market_candles_stream_time",
            "exchange",
            "symbol",
            "timeframe",
            "open_time",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(12), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    trade_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    source_event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IngestionCheckpoint(Base):
    """Durable progress and health information for one exchange stream."""

    __tablename__ = "ingestion_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "exchange",
            "symbol",
            "timeframe",
            name="ux_ingestion_checkpoint_stream",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(12), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="starting", nullable=False)
    last_closed_open_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_persisted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_backfill_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reconnect_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    backfilled_candles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    latest_version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StrategyConfigVersion(Base):
    __tablename__ = "strategy_config_versions"
    __table_args__ = (
        UniqueConstraint(
            "config_id",
            "version_number",
            name="ux_strategy_config_version_number",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    config_id: Mapped[str] = mapped_column(
        ForeignKey("strategy_configs.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(12), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    risk_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    execution_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    strategy_config_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_config_versions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    exchange: Mapped[str] = mapped_column(String(32), default="binance", nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(12), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    risk_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    execution_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    data_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
