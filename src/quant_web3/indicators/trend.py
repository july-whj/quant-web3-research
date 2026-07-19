"""Trend indicators implemented with pandas."""

from __future__ import annotations

import pandas as pd


def moving_average(values: pd.Series, window: int) -> pd.Series:
    """Return a simple moving average with a complete lookback window."""
    if window <= 0:
        raise ValueError("window must be greater than zero")
    return values.astype(float).rolling(window=window, min_periods=window).mean()
