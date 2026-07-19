import pandas as pd

from quant_web3.strategies import generate_ma_cross_signals


def test_ma_cross_position_uses_previous_signal() -> None:
    close = pd.Series(range(1, 101), dtype=float)
    frame = generate_ma_cross_signals(close, fast_window=5, slow_window=10)

    assert frame["position"].iloc[0] == 0.0
    pd.testing.assert_series_equal(
        frame["position"].iloc[1:].reset_index(drop=True),
        frame["signal"].iloc[:-1].reset_index(drop=True),
        check_names=False,
    )
