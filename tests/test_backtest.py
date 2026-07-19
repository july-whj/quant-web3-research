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
