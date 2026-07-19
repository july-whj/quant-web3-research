"""Small vectorized backtest engine for educational examples."""

from __future__ import annotations

import pandas as pd


def run_long_only_backtest(
    close: pd.Series,
    position: pd.Series,
    initial_capital: float = 1000.0,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
) -> pd.DataFrame:
    """Backtest a 0/1 position series with proportional trading costs."""
    if close.empty:
        raise ValueError("close must not be empty")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be greater than zero")
    if fee_rate < 0 or slippage_rate < 0:
        raise ValueError("fee_rate and slippage_rate cannot be negative")

    prices = close.astype(float).sort_index()
    held = position.reindex(prices.index).fillna(0.0).astype(float)
    if not held.between(0.0, 1.0).all():
        raise ValueError("position must stay between 0 and 1")

    frame = pd.DataFrame({"close": prices, "position": held})
    frame["benchmark_return"] = frame["close"].pct_change().fillna(0.0)
    frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
    frame["cost"] = frame["turnover"] * (fee_rate + slippage_rate)
    frame["strategy_return"] = (
        frame["position"] * frame["benchmark_return"] - frame["cost"]
    )
    frame["strategy_equity"] = initial_capital * (1.0 + frame["strategy_return"]).cumprod()
    frame["benchmark_equity"] = initial_capital * (
        1.0 + frame["benchmark_return"]
    ).cumprod()
    return frame
