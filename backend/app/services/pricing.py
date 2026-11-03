"""Pricing utilities – compute USD cost from token counts and model pricing."""

from __future__ import annotations

from decimal import Decimal


def compute_cost(
    input_tokens: int,
    output_tokens: int,
    input_price_per_mtok: Decimal,
    output_price_per_mtok: Decimal,
) -> Decimal:
    """Compute total cost in USD.

    Prices are per 1 million tokens.
    """
    million = Decimal("1000000")
    input_cost = (Decimal(input_tokens) / million) * input_price_per_mtok
    output_cost = (Decimal(output_tokens) / million) * output_price_per_mtok
    return (input_cost + output_cost).quantize(Decimal("0.00000001"))
