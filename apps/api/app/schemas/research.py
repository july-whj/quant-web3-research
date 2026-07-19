from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrategyParameter(BaseModel):
    name: str
    label: str
    type: Literal["integer", "number"]
    default: float | int
    minimum: float | int


class StrategyDefinition(BaseModel):
    name: str
    title: str
    description: str
    parameters: list[StrategyParameter]


class BacktestCreate(BaseModel):
    strategy_name: Literal["ma_cross_long_only"] = "ma_cross_long_only"
    symbol: Literal["BTC/USDT"] = "BTC/USDT"
    timeframe: Literal["1d"] = "1d"
    days: int = Field(default=365, ge=120, le=1000)
    parameters: dict[str, float | int]

    @model_validator(mode="after")
    def validate_parameters(self) -> BacktestCreate:
        fast = int(self.parameters.get("fast_window", 20))
        slow = int(self.parameters.get("slow_window", 60))
        fee = float(self.parameters.get("fee_rate", 0.001))
        slippage = float(self.parameters.get("slippage_rate", 0.0005))
        if fast < 2 or slow < 3 or fast >= slow:
            raise ValueError("fast_window must be >= 2 and smaller than slow_window")
        if fee < 0 or slippage < 0 or fee > 0.05 or slippage > 0.05:
            raise ValueError("fee_rate and slippage_rate must be between 0 and 0.05")
        self.parameters = {
            "fast_window": fast,
            "slow_window": slow,
            "fee_rate": fee,
            "slippage_rate": slippage,
        }
        return self


class BacktestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    strategy_name: str
    status: str
    parameters: dict[str, Any]
    summary: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    finished_at: datetime | None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    exchange: str
    symbol: str
    timeframe: str
    row_count: int
    created_at: datetime


class UsageSummary(BaseModel):
    users: int
    wallets: int
    daily_active_users: int
    monthly_active_users: int
