"""Long-only moving-average crossover strategy."""

from __future__ import annotations

import pandas as pd

from quant_web3.indicators import moving_average


def generate_ma_cross_signals(
    close: pd.Series,
    fast_window: int = 20,
    slow_window: int = 60,
) -> pd.DataFrame:
    """Build signal and next-period position for a long-only MA crossover.

    ``signal`` is known after the current candle closes. ``position`` shifts
    that signal by one period so the backtest does not trade on information
    that was unavailable at the start of the same candle.
    """
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window")
    if close.empty:
        raise ValueError("close must not be empty")

    frame = pd.DataFrame({"close": close.astype(float)}).sort_index()
    frame["fast_ma"] = moving_average(frame["close"], fast_window)
    frame["slow_ma"] = moving_average(frame["close"], slow_window)
    ready = frame[["fast_ma", "slow_ma"]].notna().all(axis=1)
    frame["signal"] = ((frame["fast_ma"] > frame["slow_ma"]) & ready).astype(float)
    frame["position"] = frame["signal"].shift(1).fillna(0.0)
    frame["trade"] = frame["position"].diff().fillna(frame["position"])
    return frame
