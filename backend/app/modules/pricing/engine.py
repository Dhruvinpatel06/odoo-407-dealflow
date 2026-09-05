"""Pricing calculation engine."""

from __future__ import annotations

from decimal import Decimal
from typing import Tuple


class PricingEngine:
    """Pure calculations for authoritative price resolution."""

    @staticmethod
    def calculate_resolved_price(
        base_unit_price: Decimal,
        variant_extra_price: Decimal = Decimal("0.00"),
        is_variant_specific_override: bool = False,
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate resolved unit price and effective variant extra price.

        If `is_variant_specific_override` is True, the variant-specific price list item
        is an all-inclusive override for the variant, so effective variant_extra_price is 0.00.
        Otherwise, if a product-level base price is used (either catalog base price or
        product-level price list override), variant_extra_price is added to base_unit_price.

        Returns (resolved_unit_price, effective_variant_extra).
        """
        if is_variant_specific_override:
            return base_unit_price, Decimal("0.00")

        effective_extra = (
            variant_extra_price if variant_extra_price is not None else Decimal("0.00")
        )
        resolved = base_unit_price + effective_extra
        return resolved, effective_extra


pricing_engine = PricingEngine()
