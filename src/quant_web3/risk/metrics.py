"""Performance metrics shared by chapters and examples."""

from __future__ import annotations

import pandas as pd


def calculate_return(initial_money: float, final_money: float) -> float:
    """Calculate the simple return between two capital values."""
    if initial_money <= 0:
        raise ValueError("initial_money must be greater than zero")
    return (final_money - initial_money) / initial_money


def total_return(equity: pd.Series) -> float:
    """Calculate total return from an equity curve."""
    clean = equity.dropna().astype(float)
    if clean.empty:
        raise ValueError("equity must contain at least one value")
    return calculate_return(clean.iloc[0], clean.iloc[-1])


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Return each point's decline from the previous equity peak."""
    clean = equity.astype(float)
    if clean.dropna().empty:
        raise ValueError("equity must contain at least one value")
    if (clean.dropna() <= 0).any():
        raise ValueError("equity values must be greater than zero")
    running_peak = clean.cummax()
    return clean / running_peak - 1.0


def max_drawdown(equity: pd.Series) -> float:
    """Return the largest peak-to-trough decline as a negative number."""
    return float(drawdown_series(equity).min())
