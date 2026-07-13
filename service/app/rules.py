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
    """Exact percentage markdown from was→now, unrounded.

    This is the value compliance decisions gate on. Keeping it unrounded is the
    PPCS-001 fix: rounding before the threshold check let a 4.6% discount round
    up to 5% and wrongly clear the genuine-discount bar.
    """
    return (promo.was_price - promo.now_price) / promo.was_price * 100


def discount_pct(promo: Promo) -> int:
    """Whole-percent markdown for display (per the API contract).

    Display only — do not gate compliance on this. Use ``raw_discount_pct``
    (via ``is_was_now_compliant``) for threshold decisions.
    """
    return round(raw_discount_pct(promo))


def is_was_now_compliant(promo: Promo) -> bool:
    """A was/now promo is compliant only if the *unrounded* markdown clears
    MIN_DISCOUNT_PCT."""
    return raw_discount_pct(promo) >= MIN_DISCOUNT_PCT
