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
    """Exact percentage markdown from was→now.

    Kept at full precision so the threshold check compares the real markdown, not
    a rounded-up one. Round only at the display edge (see ``discount_pct_display``).
    """
    return (promo.was_price - promo.now_price) / promo.was_price * 100


def discount_pct_display(promo: Promo) -> float:
    """Discount percentage rounded to one decimal for presentation only."""
    return round(discount_pct(promo), 1)


def is_was_now_compliant(promo: Promo) -> bool:
    """A was/now promo is compliant only if the markdown clears MIN_DISCOUNT_PCT.

    Compares the exact markdown against the threshold: a 4.6% discount stays below
    the 5% bar instead of being rounded up to clear it.
    """
    return discount_pct(promo) >= MIN_DISCOUNT_PCT
