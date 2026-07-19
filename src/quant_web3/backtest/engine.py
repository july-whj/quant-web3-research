"""Small vectorized backtest engine for educational examples."""

from __future__ import annotations

import pandas as pd


def run_long_only_backtest(
    close: pd.Series,
    position: pd.Series,
    initial_capital: float = 1000.0,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    *,
    open_prices: pd.Series | None = None,
) -> pd.DataFrame:
    """Backtest a 0/1 position series with proportional trading costs.

    When ``open_prices`` is supplied, position changes execute at that bar's
    open. An entry therefore earns only the open-to-close return of its first
    bar, while an exit still earns the previous-close-to-open gap.
    """
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
    if open_prices is not None:
        frame["open"] = open_prices.reindex(prices.index).astype(float)
        if frame["open"].isna().any() or (frame["open"] <= 0).any():
            raise ValueError("open_prices must align with close and stay positive")
    frame["benchmark_return"] = frame["close"].pct_change().fillna(0.0)
    frame["turnover"] = frame["position"].diff().abs().fillna(frame["position"].abs())
    frame["cost"] = frame["turnover"] * (fee_rate + slippage_rate)
    if open_prices is None:
        gross_return = frame["position"] * frame["benchmark_return"]
    else:
        previous_position = frame["position"].shift(1).fillna(0.0)
        previous_close = frame["close"].shift(1)
        overnight_return = (frame["open"] / previous_close - 1.0).fillna(0.0)
        intraday_return = frame["close"] / frame["open"] - 1.0
        # The old position earns the previous-close-to-open gap. After the
        # next-open rebalance, the new target allocation earns open-to-close.
        overnight_factor = 1.0 + previous_position * overnight_return
        intraday_factor = 1.0 + frame["position"] * intraday_return
        gross_return = overnight_factor * intraday_factor - 1.0
    frame["strategy_return"] = gross_return - frame["cost"]
    frame["strategy_equity"] = initial_capital * (1.0 + frame["strategy_return"]).cumprod()
    frame["benchmark_equity"] = initial_capital * (
        1.0 + frame["benchmark_return"]
    ).cumprod()
    return frame
