from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quant_web3.strategies import StrategyNotFoundError, strategy_registry


class StrategyDataRequirements(BaseModel):
    fields: list[str]
    market_types: list[str]
    timeframes: list[str]
    closed_candles_only: bool


class StrategyPlotDefinition(BaseModel):
    key: str
    label: str
    pane: Literal["price", "indicator"]
    color: str


class StrategyDefinition(BaseModel):
    key: str
    version: str
    kind: Literal["signal", "schedule", "grid"]
    title: str
    description: str
    default_warmup_bars: int
    data_requirements: StrategyDataRequirements
    parameters_schema: dict[str, Any]
    plots: list[StrategyPlotDefinition]


class BacktestExecutionConfig(BaseModel):
    initial_capital: float = Field(default=1000.0, gt=0, le=1_000_000_000)
    fee_rate: float = Field(default=0.001, ge=0, le=0.05)
    slippage_rate: float = Field(default=0.0005, ge=0, le=0.05)
    signal_on: Literal["candle_close"] = "candle_close"
    execute_on: Literal["next_candle_open"] = "next_candle_open"


class BacktestRiskConfig(BaseModel):
    max_position_pct: float = Field(default=1.0, gt=0, le=1.0)


class BacktestCreate(BaseModel):
    strategy_name: str = "ma_cross_long_only"
    strategy_version: str | None = None
    exchange: Literal["binance", "okx"] = "binance"
    symbol: Literal["BTC/USDT"] = "BTC/USDT"
    timeframe: Literal["1m", "5m", "15m", "1h", "4h", "1d", "1w"] = "1d"
    days: int = Field(default=365, ge=1, le=3650)
    parameters: dict[str, Any]
    risk: BacktestRiskConfig = Field(default_factory=BacktestRiskConfig)
    execution: BacktestExecutionConfig = Field(default_factory=BacktestExecutionConfig)

    @model_validator(mode="after")
    def validate_parameters(self) -> BacktestCreate:
        try:
            strategy, parameters = strategy_registry.validate_parameters(
                self.strategy_name,
                self.parameters,
                self.strategy_version,
            )
        except StrategyNotFoundError as exc:
            raise ValueError(str(exc)) from exc
        self.strategy_version = strategy.spec.version
        self.parameters = parameters.model_dump(mode="json")
        return self


class BacktestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    strategy_name: str
    strategy_version: str
    strategy_config_version_id: str | None
    exchange: str
    symbol: str
    timeframe: str
    days: int
    status: str
    parameters: dict[str, Any]
    risk_config: dict[str, Any] | None
    execution_config: dict[str, Any] | None
    data_snapshot: dict[str, Any] | None
    summary: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    finished_at: datetime | None


class StrategyConfigCreate(BacktestCreate):
    name: str = Field(min_length=1, max_length=120)


class StrategyConfigVersionCreate(BacktestCreate):
    pass


class StrategyConfigVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    config_id: str
    version_number: int
    strategy_name: str
    strategy_version: str
    exchange: str
    symbol: str
    timeframe: str
    days: int
    parameters: dict[str, Any]
    risk_config: dict[str, Any]
    execution_config: dict[str, Any]
    created_at: datetime


class StrategyConfigResponse(BaseModel):
    id: str
    name: str
    status: str
    latest_version_number: int
    created_at: datetime
    updated_at: datetime
    versions: list[StrategyConfigVersionResponse]


class StrategyConfigBacktestCreate(BaseModel):
    version_number: int | None = Field(default=None, ge=1)


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    exchange: str
    symbol: str
    timeframe: str
    row_count: int
    created_at: datetime


class MarketStreamResponse(BaseModel):
    exchange: str
    symbol: str
    timeframe: str
    status: str
    row_count: int
    last_closed_open_time: datetime | None
    last_received_at: datetime | None
    last_persisted_at: datetime | None
    last_backfill_at: datetime | None
    reconnect_count: int
    backfilled_candles: int
    last_error: str | None


class MarketCandleItem(BaseModel):
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trade_count: int | None
    source: str


class MarketCandlePageResponse(BaseModel):
    exchange: str
    symbol: str
    timeframe: str
    timezone: Literal["UTC"] = "UTC"
    items: list[MarketCandleItem]
    next_before: datetime | None
    has_more: bool


class MarketSignalItem(BaseModel):
    signal_time: datetime
    execution_time: datetime
    side: Literal["buy", "sell"]
    signal_price: Decimal
    execution_price: Decimal
    fast_ma: Decimal
    slow_ma: Decimal
    reason: Literal["ma_cross_up", "ma_cross_down"]


class MarketSignalPageResponse(BaseModel):
    exchange: str
    symbol: str
    timeframe: str
    strategy_name: Literal["ma_cross_long_only"] = "ma_cross_long_only"
    fast_window: int
    slow_window: int
    items: list[MarketSignalItem]


class StrategyPreviewRequest(BaseModel):
    strategy_version: str | None = None
    exchange: Literal["binance", "okx"] = "binance"
    symbol: Literal["BTC/USDT"] = "BTC/USDT"
    timeframe: Literal["1m", "5m", "15m", "1h", "4h", "1d", "1w"] = "1d"
    limit: int = Field(default=300, ge=100, le=1000)
    parameters: dict[str, Any]


class StrategyPreviewPoint(BaseModel):
    time: datetime
    value: Decimal


class StrategyPreviewPlot(BaseModel):
    key: str
    label: str
    pane: Literal["price", "indicator"]
    color: str
    points: list[StrategyPreviewPoint]


class StrategyPreviewSignal(BaseModel):
    signal_time: datetime
    execution_time: datetime
    side: Literal["buy", "sell"]
    signal_price: Decimal
    execution_price: Decimal
    target_position: Decimal
    position_delta: Decimal
    reason: str


class StrategyPreviewResponse(BaseModel):
    strategy_name: str
    strategy_version: str
    explanation: str
    warmup_bars: int
    candles: list[MarketCandleItem]
    plots: list[StrategyPreviewPlot]
    signals: list[StrategyPreviewSignal]


class UsageSummary(BaseModel):
    users: int
    wallets: int
    daily_active_users: int
    monthly_active_users: int
