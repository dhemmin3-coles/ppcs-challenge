"""Promotional pricing compliance rules.

Deliberately small and a little flawed — this is the surface the challenge
backlog acts on. PPCS-001 lives in `discount_pct` below.
"""
from __future__ import annotations

from dataclasses import dataclass

#: A markdown must be at least this deep to count as a genuine discount.
MIN_DISCOUNT_PCT = 5.0

#: display_channel values that present a promo to the general public (PPCS-009).
#: A member-only promo shown on any of these is a disclosure violation. Unknown
#: or missing channels are NOT treated as public, so we don't over-flag.
PUBLIC_DISPLAY_CHANNELS = {"public", "general", "storewide"}


@dataclass
class Promo:
    sku: str
    was_price: float
    now_price: float
    #: Member-pricing disclosure (PPCS-009). The rule is evaluated only when
    #: ``member_only`` is true; ``display_channel`` says how the promo is shown.
    member_only: bool = False
    display_channel: str | None = None


def discount_pct(promo: Promo) -> float:
    """Percentage markdown from was→now.

    BUG (PPCS-001): rounds to a whole percent *before* the threshold check, so a
    4.6% discount becomes 5% and wrongly clears the genuine-discount bar.
    """
    return round((promo.was_price - promo.now_price) / promo.was_price * 100)


def is_was_now_compliant(promo: Promo) -> bool:
    """A was/now promo is compliant only if the markdown clears MIN_DISCOUNT_PCT."""
    return discount_pct(promo) >= MIN_DISCOUNT_PCT


def is_member_price_rule_applicable(promo: Promo) -> bool:
    """The member-pricing disclosure rule only applies to member-only promos.

    A public promo is simply not governed by this rule (PPCS-009 AC: "Public
    offer is not affected by this rule").
    """
    return promo.member_only


def is_member_price_compliant(promo: Promo) -> bool:
    """A member-only promo must not be advertised as a general public price.

    Compliant when the promo is not member-only (rule not applicable) or when a
    member-only promo is shown on a non-public channel. An unknown or missing
    ``display_channel`` is treated as non-public, so an ambiguous label does not
    spuriously fail the promo.
    """
    if not promo.member_only:
        return True
    channel = (promo.display_channel or "").strip().lower()
    return channel not in PUBLIC_DISPLAY_CHANNELS
