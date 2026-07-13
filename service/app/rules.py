"""Promotional pricing compliance rules.

Deliberately small and a little flawed — this is the surface the challenge
backlog acts on. PPCS-001 lives in `discount_pct` below.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

#: A markdown must be at least this deep to count as a genuine discount.
MIN_DISCOUNT_PCT = 5.0

#: A promotion must run for at least this many calendar days (PPCS-006).
MIN_DURATION_DAYS = 7


@dataclass
class Promo:
    sku: str
    was_price: float
    now_price: float
    #: Optional promo window. When both are set, the duration rule applies.
    start_date: date | None = None
    end_date: date | None = None


def discount_pct(promo: Promo) -> float:
    """Percentage markdown from was→now.

    BUG (PPCS-001): rounds to a whole percent *before* the threshold check, so a
    4.6% discount becomes 5% and wrongly clears the genuine-discount bar.
    """
    return round((promo.was_price - promo.now_price) / promo.was_price * 100)


def is_was_now_compliant(promo: Promo) -> bool:
    """A was/now promo is compliant only if the markdown clears MIN_DISCOUNT_PCT."""
    return discount_pct(promo) >= MIN_DISCOUNT_PCT


def promo_duration_days(promo: Promo) -> int | None:
    """Length of the promo window in calendar days, counted *inclusively*.

    Returns ``None`` when either date is missing (the duration rule does not
    apply). A promo running 2026-07-13..2026-07-19 spans 7 days, not 6: we add
    one to the exclusive ``timedelta`` difference so both the start and end
    date count. This is the inclusive/exclusive trap PPCS-006 warns about.
    """
    if promo.start_date is None or promo.end_date is None:
        return None
    return (promo.end_date - promo.start_date).days + 1


def is_duration_compliant(promo: Promo) -> bool:
    """A promo is duration-compliant if it runs at least MIN_DURATION_DAYS.

    When no window is supplied the rule is not evaluated, and the promo is
    treated as compliant so a was/now-only submission is not spuriously failed.
    """
    days = promo_duration_days(promo)
    if days is None:
        return True
    return days >= MIN_DURATION_DAYS
