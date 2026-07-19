"""Reusable paper-trading calculations without exchange credentials."""

from .costs import (
    estimate_cex_limit_fill,
    estimate_cex_market_fill,
    quantize_amount,
    quantize_price,
)
from .grid import build_grid_levels, order_touched_by_candle
from .models import GridLevel, GridMode, PaperFillEstimate, PaperSide

__all__ = [
    "GridLevel",
    "GridMode",
    "PaperFillEstimate",
    "PaperSide",
    "build_grid_levels",
    "estimate_cex_limit_fill",
    "estimate_cex_market_fill",
    "order_touched_by_candle",
    "quantize_amount",
    "quantize_price",
]
