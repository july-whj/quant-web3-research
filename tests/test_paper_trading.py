from decimal import Decimal

import pytest

from quant_web3.paper_trading import (
    build_grid_levels,
    estimate_cex_market_fill,
    order_touched_by_candle,
)


def test_market_fill_applies_fee_and_directional_slippage() -> None:
    buy = estimate_cex_market_fill(
        side="buy",
        reference_price=Decimal("100"),
        quantity=Decimal("2"),
        fee_rate=Decimal("0.001"),
        slippage_rate=Decimal("0.01"),
    )
    sell = estimate_cex_market_fill(
        side="sell",
        reference_price=Decimal("100"),
        quantity=Decimal("2"),
        fee_rate=Decimal("0.001"),
        slippage_rate=Decimal("0.01"),
    )

    assert buy.execution_price == Decimal("101.00000000")
    assert buy.quote_amount == Decimal("202.00000000")
    assert buy.fee_amount == Decimal("0.20200000")
    assert sell.execution_price == Decimal("99.00000000")
    assert sell.gas_amount == 0


def test_grid_levels_include_both_boundaries() -> None:
    levels = build_grid_levels(Decimal("80"), Decimal("120"), 4)

    assert [level.price for level in levels] == [
        Decimal("80.00000000"),
        Decimal("90.00000000"),
        Decimal("100.00000000"),
        Decimal("110.00000000"),
        Decimal("120.00000000"),
    ]


@pytest.mark.parametrize(
    ("side", "price", "expected"),
    [("buy", "95", True), ("buy", "85", False), ("sell", "105", True), ("sell", "115", False)],
)
def test_limit_order_touch_rule(side: str, price: str, expected: bool) -> None:
    assert order_touched_by_candle(
        side=side,
        limit_price=Decimal(price),
        candle_low=Decimal("90"),
        candle_high=Decimal("110"),
    ) is expected
