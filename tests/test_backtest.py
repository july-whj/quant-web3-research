import pandas as pd
import pytest

from quant_web3.backtest import run_long_only_backtest


def test_zero_position_keeps_initial_capital() -> None:
    close = pd.Series([100.0, 110.0, 90.0])
    position = pd.Series([0.0, 0.0, 0.0])
    result = run_long_only_backtest(close, position, initial_capital=1000.0)
    assert result["strategy_equity"].iloc[-1] == pytest.approx(1000.0)


def test_entry_cost_is_deducted() -> None:
    close = pd.Series([100.0, 100.0])
    position = pd.Series([0.0, 1.0])
    result = run_long_only_backtest(
        close,
        position,
        initial_capital=1000.0,
        fee_rate=0.001,
        slippage_rate=0.001,
    )
    assert result["strategy_equity"].iloc[-1] == pytest.approx(998.0)


def test_next_open_execution_does_not_earn_pre_entry_gap() -> None:
    index = pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC")
    close = pd.Series([100.0, 120.0, 120.0], index=index)
    open_prices = pd.Series([100.0, 110.0, 120.0], index=index)
    position = pd.Series([0.0, 1.0, 1.0], index=index)

    result = run_long_only_backtest(
        close,
        position,
        open_prices=open_prices,
        fee_rate=0,
        slippage_rate=0,
    )

    assert result["strategy_return"].iloc[1] == pytest.approx(120 / 110 - 1)
    assert result["benchmark_return"].iloc[1] == pytest.approx(0.2)


def test_next_open_execution_supports_fractional_target_positions() -> None:
    index = pd.date_range("2026-01-01", periods=2, freq="D", tz="UTC")
    close = pd.Series([100.0, 110.0], index=index)
    open_prices = pd.Series([100.0, 100.0], index=index)
    position = pd.Series([0.0, 0.5], index=index)

    result = run_long_only_backtest(
        close,
        position,
        open_prices=open_prices,
        fee_rate=0,
        slippage_rate=0,
    )

    assert result["strategy_return"].iloc[1] == pytest.approx(0.05)
