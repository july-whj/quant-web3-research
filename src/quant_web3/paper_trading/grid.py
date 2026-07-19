"""Grid construction and candle-touch rules used by the paper engine."""

from __future__ import annotations

from decimal import Decimal

from .costs import quantize_price
from .models import GridLevel, GridMode, PaperSide


def build_grid_levels(
    lower_price: Decimal,
    upper_price: Decimal,
    grid_count: int,
    mode: GridMode = "arithmetic",
) -> list[GridLevel]:
    if lower_price <= 0 or upper_price <= lower_price:
        raise ValueError("upper_price must be greater than lower_price")
    if not 2 <= grid_count <= 100:
        raise ValueError("grid_count must stay between 2 and 100")

    if mode == "arithmetic":
        step = (upper_price - lower_price) / grid_count
        prices = [lower_price + step * index for index in range(grid_count + 1)]
    elif mode == "geometric":
        ratio = (float(upper_price / lower_price)) ** (1 / grid_count)
        prices = [lower_price * Decimal(str(ratio**index)) for index in range(grid_count + 1)]
    else:
        raise ValueError("mode must be arithmetic or geometric")
    return [GridLevel(index=index, price=quantize_price(price)) for index, price in enumerate(prices)]


def order_touched_by_candle(
    *,
    side: PaperSide,
    limit_price: Decimal,
    candle_low: Decimal,
    candle_high: Decimal,
) -> bool:
    if side == "buy":
        return candle_low <= limit_price
    if side == "sell":
        return candle_high >= limit_price
    raise ValueError("side must be buy or sell")
