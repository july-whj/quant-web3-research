"""Versioned trading strategies and their compatibility helpers."""

from .base import Strategy
from .builtins import (
    AdaptiveGridStrategy,
    DcaParameters,
    DcaStrategy,
    GridParameters,
    MaCrossParameters,
    MaCrossStrategy,
    RsiReversalParameters,
    RsiReversalStrategy,
    generate_ma_cross_signals,
)
from .models import MarketDataRequirements, StrategyPlot, StrategySpec
from .registry import StrategyNotFoundError, strategy_registry


strategy_registry.register(MaCrossStrategy())
strategy_registry.register(RsiReversalStrategy())
strategy_registry.register(DcaStrategy())
strategy_registry.register(AdaptiveGridStrategy())

__all__ = [
    "AdaptiveGridStrategy",
    "DcaParameters",
    "DcaStrategy",
    "GridParameters",
    "MaCrossParameters",
    "MaCrossStrategy",
    "MarketDataRequirements",
    "Strategy",
    "StrategyNotFoundError",
    "StrategyPlot",
    "StrategySpec",
    "RsiReversalParameters",
    "RsiReversalStrategy",
    "generate_ma_cross_signals",
    "strategy_registry",
]
