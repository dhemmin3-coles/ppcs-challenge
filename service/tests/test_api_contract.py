import pytest
from fastapi.responses import JSONResponse

from app.main import PromoIn, validate


def test_validate_returns_existing_verdict_shape():
    response = validate(PromoIn(sku="SKU-OK", was_price=10.00, now_price=9.00))

    assert response == {
        "sku": "SKU-OK",
        "discount_pct": 10,
        "was_now_compliant": True,
    }


def test_validate_reports_marginal_discount_after_ppcs_001_fix():
    # 4.6% markdown: previously rounded up to 5% and wrongly passed (PPCS-001).
    # After the fix it is reported at true precision and fails the 5% bar.
    response = validate(PromoIn(sku="SKU-1", was_price=10.00, now_price=9.54))

    assert response == {
        "sku": "SKU-1",
        "discount_pct": 4.6,
        "was_now_compliant": False,
    }


@pytest.mark.parametrize(
    "was_price,now_price,expected_fragment",
    [
        (0, 5.00, "was_price"),
        (-1, 5.00, "was_price"),
        (10.00, -1.00, "now_price"),
        (10.00, 15.00, "now_price"),
    ],
)
def test_validate_rejects_invalid_prices(was_price, now_price, expected_fragment):
    response = validate(PromoIn(sku="SKU-BAD", was_price=was_price, now_price=now_price))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 422
    import json
    body = json.loads(response.body)
    assert expected_fragment in body["error"]
