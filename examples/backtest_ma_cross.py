"""Run a deterministic MA-cross backtest without downloading market data."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_web3.backtest import run_long_only_backtest
from quant_web3.reporting import summarize_backtest
from quant_web3.strategies import generate_ma_cross_signals


def build_demo_prices(periods: int = 300) -> pd.Series:
    """Create repeatable sample prices with alternating market regimes."""
    rng = np.random.default_rng(42)
    index = pd.date_range("2025-01-01", periods=periods, freq="D", tz="UTC")
    regime = np.concatenate(
        [
            np.full(100, 0.0020),
            np.full(100, -0.0018),
            np.full(periods - 200, 0.0012),
        ]
    )
    daily_return = regime + rng.normal(0.0, 0.012, size=periods)
    prices = 60_000 * np.exp(np.cumsum(daily_return))
    return pd.Series(prices, index=index, name="close")


def main() -> None:
    close = build_demo_prices()
    signals = generate_ma_cross_signals(close, fast_window=20, slow_window=60)
    result = run_long_only_backtest(
        close=signals["close"],
        position=signals["position"],
        initial_capital=1000.0,
        fee_rate=0.001,
        slippage_rate=0.0005,
    )
    summary = summarize_backtest(result)

    print("MA20/MA60 demo backtest")
    print(f"Strategy return: {summary['strategy_return']:.2%}")
    print(f"Benchmark return: {summary['benchmark_return']:.2%}")
    print(f"Strategy max drawdown: {summary['strategy_max_drawdown']:.2%}")
    print(f"Trades: {summary['trade_count']}")


if __name__ == "__main__":
    main()
