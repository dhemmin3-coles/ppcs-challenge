from app.main import PromoIn, validate


def test_validate_returns_existing_verdict_shape():
    response = validate(PromoIn(sku="SKU-OK", was_price=10.00, now_price=9.00))

    assert response == {
        "sku": "SKU-OK",
        "discount_pct": 10,
        "was_now_compliant": True,
    }


def test_validate_marginal_discount_displays_rounded_but_is_non_compliant():
    # PPCS-001: was=$10.00 -> now=$9.54 is a 4.6% markdown.
    # discount_pct stays a rounded whole-percent DISPLAY value (5) per the API
    # contract, but compliance gates on the unrounded 4.6% and is False.
    response = validate(PromoIn(sku="SKU-1", was_price=10.00, now_price=9.54))

    assert response == {
        "sku": "SKU-1",
        "discount_pct": 5,
        "was_now_compliant": False,
    }
