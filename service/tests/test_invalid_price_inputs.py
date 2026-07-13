"""PPCS-004 — invalid promo prices are rejected with a clear 400.

An impossible price relationship must return a client error, not be evaluated as
a normal pass/fail compliance verdict.
"""
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_was_price_zero_is_rejected():
    response = client.post(
        "/validate", json={"sku": "SKU-1", "was_price": 0.0, "now_price": 0.0}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "invalid_was_price"


def test_was_price_negative_is_rejected():
    response = client.post(
        "/validate", json={"sku": "SKU-1", "was_price": -10.0, "now_price": 5.0}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "invalid_was_price"


def test_now_price_negative_is_rejected():
    response = client.post(
        "/validate", json={"sku": "SKU-1", "was_price": 10.0, "now_price": -1.0}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "invalid_now_price"


def test_now_price_above_was_price_is_rejected():
    response = client.post(
        "/validate", json={"sku": "SKU-1", "was_price": 10.0, "now_price": 12.0}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "now_price_exceeds_was_price"


def test_valid_promo_still_returns_existing_verdict_shape():
    response = client.post(
        "/validate", json={"sku": "SKU-OK", "was_price": 10.0, "now_price": 9.0}
    )

    assert response.status_code == 200
    assert response.json() == {
        "sku": "SKU-OK",
        "discount_pct": 10,
        "was_now_compliant": True,
    }


def test_now_price_zero_is_a_valid_free_item():
    # AC says now_price < 0 is rejected — exactly 0 (a free item) is still valid.
    response = client.post(
        "/validate", json={"sku": "SKU-FREE", "was_price": 10.0, "now_price": 0.0}
    )

    assert response.status_code == 200
    assert response.json()["was_now_compliant"] is True
