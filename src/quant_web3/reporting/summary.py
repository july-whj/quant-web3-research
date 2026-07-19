"""Convert a backtest result into a compact summary."""

from __future__ import annotations

import pandas as pd

from quant_web3.risk import max_drawdown, total_return


def summarize_backtest(result: pd.DataFrame) -> dict[str, float | int]:
    """Summarize strategy and benchmark return, drawdown and trades."""
    required = {"strategy_equity", "benchmark_equity", "turnover"}
    missing = required.difference(result.columns)
    if missing:
        raise ValueError(f"missing result columns: {sorted(missing)}")

    return {
        "strategy_return": total_return(result["strategy_equity"]),
        "benchmark_return": total_return(result["benchmark_equity"]),
        "strategy_max_drawdown": max_drawdown(result["strategy_equity"]),
        "benchmark_max_drawdown": max_drawdown(result["benchmark_equity"]),
        "trade_count": int((result["turnover"] > 0).sum()),
    }
