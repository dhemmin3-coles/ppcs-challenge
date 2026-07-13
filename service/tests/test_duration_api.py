"""PPCS-006 — /validate wiring for the duration rule.

The stable /validate contract (tests/test_api_contract.py) asserts an exact
response dict with no duration key. So `duration_compliant` must appear *only*
when both dates are supplied; a dates-less request keeps the original shape.
"""
from app.main import PromoIn, validate


def test_validate_omits_duration_when_no_dates():
    response = validate(PromoIn(sku="SKU-OK", was_price=10.00, now_price=9.00))
    assert "duration_compliant" not in response
    assert response == {
        "sku": "SKU-OK",
        "discount_pct": 10,
        "was_now_compliant": True,
    }


def test_validate_reports_duration_compliant_for_seven_day_promo():
    response = validate(
        PromoIn(
            sku="SKU-7D",
            was_price=10.00,
            now_price=9.00,
            start_date="2026-07-13",
            end_date="2026-07-19",
        )
    )
    assert response["duration_compliant"] is True
    assert response["was_now_compliant"] is True


def test_validate_reports_duration_non_compliant_for_six_day_promo():
    response = validate(
        PromoIn(
            sku="SKU-6D",
            was_price=10.00,
            now_price=9.00,
            start_date="2026-07-13",
            end_date="2026-07-18",
        )
    )
    assert response["duration_compliant"] is False
    # was/now still evaluated and independent
    assert response["was_now_compliant"] is True
