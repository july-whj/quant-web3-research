"""Shared contracts for discoverable, versioned trading strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from pydantic import BaseModel


StrategyKind = Literal["signal", "schedule", "grid"]


@dataclass(frozen=True)
class StrategyPlot:
    key: str
    label: str
    pane: Literal["price", "indicator"]
    color: str


@dataclass(frozen=True)
class MarketDataRequirements:
    """Market-data capabilities required before a strategy can run."""

    fields: tuple[str, ...]
    market_types: tuple[str, ...] = ("spot",)
    timeframes: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "1d", "1w")
    closed_candles_only: bool = True


@dataclass(frozen=True)
class StrategySpec:
    """The single source of truth shared by API validation and Web forms."""

    key: str
    version: str
    title: str
    description: str
    kind: StrategyKind
    parameters_model: type[BaseModel]
    data_requirements: MarketDataRequirements
    warmup_bars: Callable[[BaseModel], int]
    plots: tuple[StrategyPlot, ...]
    explain: Callable[[BaseModel], str]

    def parameter_schema(self) -> dict[str, object]:
        return self.parameters_model.model_json_schema()

    def validate_parameters(self, values: dict[str, object] | BaseModel) -> BaseModel:
        if isinstance(values, self.parameters_model):
            return values
        if isinstance(values, BaseModel):
            values = values.model_dump()
        return self.parameters_model.model_validate(values)

    def required_warmup_bars(self, values: dict[str, object] | BaseModel) -> int:
        return int(self.warmup_bars(self.validate_parameters(values)))

    def default_warmup_bars(self) -> int:
        return self.required_warmup_bars({})

    def explanation(self, values: dict[str, object] | BaseModel) -> str:
        return self.explain(self.validate_parameters(values))
