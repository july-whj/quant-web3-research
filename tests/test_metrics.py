import pandas as pd
import pytest

from quant_web3.risk import calculate_return, max_drawdown, total_return


def test_calculate_return() -> None:
    assert calculate_return(1000, 1100) == pytest.approx(0.10)


def test_total_return() -> None:
    equity = pd.Series([1000.0, 900.0, 1200.0])
    assert total_return(equity) == pytest.approx(0.20)


def test_max_drawdown_uses_previous_peak() -> None:
    equity = pd.Series([100.0, 120.0, 90.0, 130.0])
    assert max_drawdown(equity) == pytest.approx(-0.25)
