import pandas as pd
import pytest
from pydantic import ValidationError

from quant_web3.strategies import generate_ma_cross_signals, strategy_registry


def test_ma_cross_position_uses_previous_signal() -> None:
    close = pd.Series(range(1, 101), dtype=float)
    frame = generate_ma_cross_signals(close, fast_window=5, slow_window=10)

    assert frame["position"].iloc[0] == 0.0
    pd.testing.assert_series_equal(
        frame["position"].iloc[1:].reset_index(drop=True),
        frame["signal"].iloc[:-1].reset_index(drop=True),
        check_names=False,
    )


def test_registry_validates_and_normalizes_strategy_parameters() -> None:
    strategy, parameters = strategy_registry.validate_parameters(
        "ma_cross_long_only",
        {"fast_window": 10, "slow_window": 30},
    )

    assert strategy.spec.version == "1.0.0"
    assert parameters.model_dump() == {"fast_window": 10, "slow_window": 30}
    assert strategy.spec.required_warmup_bars(parameters) == 30


def test_strategy_parameters_do_not_accept_execution_costs() -> None:
    with pytest.raises(ValidationError):
        strategy_registry.validate_parameters(
            "ma_cross_long_only",
            {
                "fast_window": 20,
                "slow_window": 60,
                "fee_rate": 0.001,
            },
        )


def test_all_built_in_strategies_produce_bounded_next_bar_positions() -> None:
    index = pd.date_range("2025-01-01", periods=240, freq="D", tz="UTC")
    close = pd.Series(
        [100 + index_value * 0.08 + 12 * ((index_value % 40) / 40 - 0.5) for index_value in range(240)],
        index=index,
        dtype=float,
    )
    candles = pd.DataFrame({"close": close})

    for strategy in strategy_registry.list():
        parameters = strategy.spec.validate_parameters({})
        frame = strategy.generate_signals(candles, parameters)

        assert frame["position"].between(0, 1).all(), strategy.spec.key
        assert frame["position"].iloc[0] == 0
        pd.testing.assert_series_equal(
            frame["position"].iloc[1:].reset_index(drop=True),
            frame["signal"].iloc[:-1].reset_index(drop=True),
            check_names=False,
        )


def test_registry_exposes_four_versioned_built_in_strategies() -> None:
    assert {strategy.spec.key for strategy in strategy_registry.list()} == {
        "ma_cross_long_only",
        "rsi_reversal_long_only",
        "staged_dca_long_only",
        "adaptive_spot_grid",
    }
    assert all(strategy.spec.version == "1.0.0" for strategy in strategy_registry.list())
