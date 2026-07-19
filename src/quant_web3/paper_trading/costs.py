"""Deterministic CEX execution-cost calculations for simulated fills."""

from __future__ import annotations

from decimal import Decimal

from .models import PaperFillEstimate, PaperSide


PRICE_QUANTUM = Decimal("0.00000001")
AMOUNT_QUANTUM = Decimal("0.00000001")


def quantize_price(value: Decimal) -> Decimal:
    return value.quantize(PRICE_QUANTUM)


def quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(AMOUNT_QUANTUM)


def estimate_cex_market_fill(
    *,
    side: PaperSide,
    reference_price: Decimal,
    quantity: Decimal,
    fee_rate: Decimal,
    slippage_rate: Decimal,
) -> PaperFillEstimate:
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    if reference_price <= 0 or quantity <= 0:
        raise ValueError("reference_price and quantity must be greater than zero")
    if fee_rate < 0 or slippage_rate < 0:
        raise ValueError("cost rates cannot be negative")

    direction = Decimal("1") if side == "buy" else Decimal("-1")
    execution_price = quantize_price(
        reference_price * (Decimal("1") + direction * slippage_rate)
    )
    quote_amount = quantize_amount(execution_price * quantity)
    fee_amount = quantize_amount(quote_amount * fee_rate)
    slippage_amount = quantize_amount(abs(execution_price - reference_price) * quantity)
    return PaperFillEstimate(
        side=side,
        reference_price=quantize_price(reference_price),
        execution_price=execution_price,
        quantity=quantize_amount(quantity),
        quote_amount=quote_amount,
        fee_amount=fee_amount,
        slippage_amount=slippage_amount,
    )


def estimate_cex_limit_fill(
    *,
    side: PaperSide,
    limit_price: Decimal,
    quantity: Decimal,
    fee_rate: Decimal,
) -> PaperFillEstimate:
    """A resting limit order fills at its limit price with no synthetic slippage."""

    if limit_price <= 0 or quantity <= 0:
        raise ValueError("limit_price and quantity must be greater than zero")
    quote_amount = quantize_amount(limit_price * quantity)
    return PaperFillEstimate(
        side=side,
        reference_price=quantize_price(limit_price),
        execution_price=quantize_price(limit_price),
        quantity=quantize_amount(quantity),
        quote_amount=quote_amount,
        fee_amount=quantize_amount(quote_amount * fee_rate),
        slippage_amount=Decimal("0"),
    )
