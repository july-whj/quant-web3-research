"""Pure domain values shared by the paper-trading API and worker."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


PaperSide = Literal["buy", "sell"]
GridMode = Literal["arithmetic", "geometric"]


@dataclass(frozen=True)
class PaperFillEstimate:
    side: PaperSide
    reference_price: Decimal
    execution_price: Decimal
    quantity: Decimal
    quote_amount: Decimal
    fee_amount: Decimal
    slippage_amount: Decimal
    gas_amount: Decimal = Decimal("0")


@dataclass(frozen=True)
class GridLevel:
    index: int
    price: Decimal
