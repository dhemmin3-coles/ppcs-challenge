"""Promotional pricing compliance rules.

Deliberately small and a little flawed — this is the surface the challenge
backlog acts on. PPCS-001 lives in `discount_pct` below.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

#: A markdown must be at least this deep to count as a genuine discount.
MIN_DISCOUNT_PCT = 5.0


@dataclass
class Promo:
    sku: str
    was_price: float
    now_price: float


def discount_pct(promo: Promo) -> float:
    """Percentage markdown from was→now.

    BUG (PPCS-001): rounds to a whole percent *before* the threshold check, so a
    4.6% discount becomes 5% and wrongly clears the genuine-discount bar.
    """
    return round((promo.was_price - promo.now_price) / promo.was_price * 100)


def is_was_now_compliant(promo: Promo) -> bool:
    """A was/now promo is compliant only if the markdown clears MIN_DISCOUNT_PCT."""
    return discount_pct(promo) >= MIN_DISCOUNT_PCT


@dataclass
class MultiBuy:
    """A multi-buy offer, e.g. "3 for $10.00"."""

    quantity: int
    bundle_price: float


def effective_unit_price(offer: MultiBuy) -> float:
    """Effective per-unit price for a multi-buy offer.

    ``3 for 10.00`` returns ``3.33`` using normal currency rounding (2 dp,
    round half up). Rejects a non-positive/non-integer quantity or a
    non-positive bundle price.
    """
    if not isinstance(offer.quantity, int) or offer.quantity <= 0:
        raise ValueError("quantity must be a positive integer")
    if offer.bundle_price <= 0:
        raise ValueError("bundle_price must be positive")

    unit = Decimal(str(offer.bundle_price)) / Decimal(offer.quantity)
    return float(unit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
