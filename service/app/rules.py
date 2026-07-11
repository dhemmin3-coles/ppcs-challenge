"""Promotional pricing compliance rules.

Deliberately small and a little flawed — this is the surface the challenge
backlog acts on. PPCS-001 lives in `discount_pct` below.
"""
from __future__ import annotations

from dataclasses import dataclass

#: A markdown must be at least this deep to count as a genuine discount.
MIN_DISCOUNT_PCT = 5.0


@dataclass
class Promo:
    sku: str
    was_price: float
    now_price: float


def discount_pct(promo: Promo) -> float:
    """Percentage markdown from was→now.

    Keep precision for compliance checks. Presentation rounding belongs at the
    API/UI boundary, not in the rule itself.
    """
    return (promo.was_price - promo.now_price) / promo.was_price * 100


def is_was_now_compliant(promo: Promo) -> bool:
    """A was/now promo is compliant only if the markdown clears MIN_DISCOUNT_PCT."""
    return discount_pct(promo) >= MIN_DISCOUNT_PCT
