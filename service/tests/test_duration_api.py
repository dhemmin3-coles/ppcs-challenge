"""PPCS-006 — /validate wiring for the duration rule.

The stable /validate contract (tests/test_api_contract.py) asserts an exact
response dict with no duration key. So `duration_compliant` must appear *only*
when both dates are supplied; a dates-less request keeps the original shape.
"""
from fastapi.testclient import TestClient

from app.main import PromoIn, app, validate


client = TestClient(app)


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


# --- window validation over the real HTTP route (PPCS-006 hardening) --------
# The ticket warns against date-arithmetic shortcuts. A backwards or
# half-specified window is a client error, not a silently non-compliant promo.


def test_inverted_window_is_rejected_with_400():
    response = client.post(
        "/validate",
        json={
            "sku": "SKU-INV",
            "was_price": 10.00,
            "now_price": 9.00,
            "start_date": "2026-07-19",
            "end_date": "2026-07-13",  # end before start
        },
    )
    assert response.status_code == 400
    assert "end_date" in response.json()["detail"]


def test_half_specified_window_is_rejected_with_400():
    # start without end: the duration rule cannot be evaluated as intended, so
    # reject rather than silently skip it.
    response = client.post(
        "/validate",
        json={
            "sku": "SKU-HALF",
            "was_price": 10.00,
            "now_price": 9.00,
            "start_date": "2026-07-13",
        },
    )
    assert response.status_code == 400
    assert "together" in response.json()["detail"]


def test_equal_dates_are_valid_but_duration_non_compliant():
    # start == end is a legitimate one-day window (not inverted): 200, and the
    # duration rule fails it (1 day < 7).
    response = client.post(
        "/validate",
        json={
            "sku": "SKU-1D",
            "was_price": 10.00,
            "now_price": 9.00,
            "start_date": "2026-07-13",
            "end_date": "2026-07-13",
        },
    )
    assert response.status_code == 200
    assert response.json()["duration_compliant"] is False
