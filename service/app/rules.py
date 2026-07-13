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


def raw_discount_pct(promo: Promo) -> float:
    """Exact (unrounded) percentage markdown from was->now.

    This is the value compliance decisions must use. It is intentionally NOT
    rounded so a marginal markdown cannot be nudged over the threshold.
    """
    return (promo.was_price - promo.now_price) / promo.was_price * 100


def discount_pct(promo: Promo) -> int:
    """Rounded whole-percent markdown, for **display only**.

    Per the API contract, `discount_pct` is a display value rounded to a whole
    percent. It must NOT be used as the compliance threshold gate.

    BUG FIX (PPCS-001): the previous implementation used this rounded value for
    the threshold check too, so a 4.6% discount rounded up to 5% and wrongly
    cleared the genuine-discount bar. Compliance now gates on the unrounded
    `raw_discount_pct` while this stays a display value.
    """
    return round(raw_discount_pct(promo))


def is_was_now_compliant(promo: Promo) -> bool:
    """A was/now promo is compliant only if the markdown clears MIN_DISCOUNT_PCT.

    Gates on the unrounded markdown so marginal discounts below the threshold
    are correctly rejected (PPCS-001).
    """
    return raw_discount_pct(promo) >= MIN_DISCOUNT_PCT
