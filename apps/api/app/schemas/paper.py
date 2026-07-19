from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PaperAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    exchange: Literal["binance", "okx"] = "binance"
    initial_funds: Decimal = Field(default=Decimal("10000"), ge=100, le=10_000_000)
    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=Decimal("0.05"))
    slippage_rate: Decimal = Field(default=Decimal("0.0005"), ge=0, le=Decimal("0.05"))
    max_position_pct: Decimal = Field(default=Decimal("1"), gt=0, le=1)
    max_order_notional: Decimal = Field(default=Decimal("1000000"), gt=0)


class PaperFundsCreate(BaseModel):
    amount: Decimal = Field(gt=0, le=10_000_000)
    note: str | None = Field(default=None, max_length=160)


class PaperOrderCreate(BaseModel):
    client_order_id: str | None = Field(default=None, max_length=64)
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: Decimal = Field(gt=0, le=100_000)
    limit_price: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_limit_price(self) -> PaperOrderCreate:
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("限价单必须提供 limit_price")
        if self.order_type == "market" and self.limit_price is not None:
            raise ValueError("市价单不能提供 limit_price")
        return self


class PaperGridCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    lower_price: Decimal = Field(gt=0)
    upper_price: Decimal = Field(gt=0)
    grid_count: int = Field(default=8, ge=2, le=50)
    grid_mode: Literal["arithmetic", "geometric"] = "arithmetic"
    investment: Decimal = Field(gt=0, le=10_000_000)

    @model_validator(mode="after")
    def validate_range(self) -> PaperGridCreate:
        if self.upper_price <= self.lower_price:
            raise ValueError("upper_price 必须大于 lower_price")
        return self


class PaperBalanceResponse(BaseModel):
    asset: str
    available: Decimal
    locked: Decimal


class PaperPositionResponse(BaseModel):
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    mark_price: Decimal
    market_value: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class PaperAccountResponse(BaseModel):
    id: str
    name: str
    exchange: str
    symbol: str
    status: str
    fee_rate: Decimal
    slippage_rate: Decimal
    max_position_pct: Decimal
    max_order_notional: Decimal
    balances: list[PaperBalanceResponse]
    position: PaperPositionResponse
    equity: Decimal
    total_fees: Decimal
    total_gas: Decimal
    created_at: datetime


class PaperOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    bot_id: str | None
    client_order_id: str
    side: str
    order_type: str
    status: str
    quantity: Decimal
    limit_price: Decimal | None
    filled_quantity: Decimal
    average_price: Decimal | None
    fee_amount: Decimal
    slippage_amount: Decimal
    gas_amount: Decimal
    grid_level: int | None
    rejection_reason: str | None
    created_at: datetime
    filled_at: datetime | None


class PaperFillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    side: str
    reference_price: Decimal
    execution_price: Decimal
    quantity: Decimal
    quote_amount: Decimal
    fee_amount: Decimal
    slippage_amount: Decimal
    gas_amount: Decimal
    market_time: datetime
    created_at: datetime


class PaperLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset: str
    entry_type: str
    amount: Decimal
    available_after: Decimal
    locked_after: Decimal
    reference_type: str | None
    reference_id: str | None
    description: str | None
    created_at: datetime


class PaperBotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    name: str
    bot_type: str
    status: str
    lower_price: Decimal
    upper_price: Decimal
    grid_count: int
    grid_mode: str
    investment: Decimal
    parameters: dict[str, Any]
    realized_profit: Decimal
    created_at: datetime
    started_at: datetime | None
    stopped_at: datetime | None


class PaperSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    market_time: datetime
    equity: Decimal
    quote_balance: Decimal
    base_quantity: Decimal
    mark_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
