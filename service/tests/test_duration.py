"""PPCS-006 — minimum promotion duration rule.

The rule: a promo must run for at least 7 calendar days, counted *inclusively*
of both the start and end date (see service/api-contract.md). The boundary that
matters is the off-by-one trap the ticket warns about: a naive
`(end - start).days` is exclusive of the end date, so it counts a genuinely
7-day promo as 6.
"""
from datetime import date

from app.rules import (
    Promo,
    is_duration_compliant,
    is_was_now_compliant,
    promo_duration_days,
)


def test_seven_day_promo_is_compliant():
    # 2026-07-13 .. 2026-07-19 inclusive == 7 calendar days.
    promo = Promo(
        "A",
        was_price=10.00,
        now_price=9.00,
        start_date=date(2026, 7, 13),
        end_date=date(2026, 7, 19),
    )
    assert promo_duration_days(promo) == 7
    assert is_duration_compliant(promo) is True


def test_six_day_promo_is_not_compliant():
    # 2026-07-13 .. 2026-07-18 inclusive == 6 calendar days.
    promo = Promo(
        "B",
        was_price=10.00,
        now_price=9.00,
        start_date=date(2026, 7, 13),
        end_date=date(2026, 7, 18),
    )
    assert promo_duration_days(promo) == 6
    assert is_duration_compliant(promo) is False


def test_single_day_promo_is_not_compliant():
    # start == end is a one-day promo, not a zero-day one (inclusive counting).
    promo = Promo(
        "C",
        was_price=10.00,
        now_price=9.00,
        start_date=date(2026, 7, 13),
        end_date=date(2026, 7, 13),
    )
    assert promo_duration_days(promo) == 1
    assert is_duration_compliant(promo) is False


def test_duration_not_evaluated_when_dates_absent():
    # No dates supplied -> duration rule does not apply; treat as compliant so a
    # was/now-only promo is not spuriously failed.
    promo = Promo("D", was_price=10.00, now_price=9.00)
    assert promo_duration_days(promo) is None
    assert is_duration_compliant(promo) is True


def test_was_now_compliance_is_independent_of_duration():
    # A deep discount over too short a window: was/now passes, duration fails.
    promo = Promo(
        "E",
        was_price=20.00,
        now_price=15.00,  # 25% markdown -> was/now compliant
        start_date=date(2026, 7, 13),
        end_date=date(2026, 7, 15),  # 3 days -> duration non-compliant
    )
    assert is_was_now_compliant(promo) is True
    assert is_duration_compliant(promo) is False


def test_combined_failure_both_rules_fail():
    # Shallow discount AND too short: both rules independently fail.
    promo = Promo(
        "F",
        was_price=100.00,
        now_price=98.00,  # 2% markdown -> was/now non-compliant
        start_date=date(2026, 7, 13),
        end_date=date(2026, 7, 16),  # 4 days -> duration non-compliant
    )
    assert is_was_now_compliant(promo) is False
    assert is_duration_compliant(promo) is False
