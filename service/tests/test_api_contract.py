from app.main import PromoIn, validate


def test_validate_returns_existing_verdict_shape():
    response = validate(PromoIn(sku="SKU-OK", was_price=10.00, now_price=9.00))

    assert response == {
        "sku": "SKU-OK",
        "discount_pct": 10,
        "was_now_compliant": True,
    }


def test_validate_rejects_marginal_discount_below_threshold():
    # PPCS-001: a 4.6% markdown must report the true percent and fail the 5%
    # genuine-discount bar (previously rounded up to 5% and wrongly passed).
    response = validate(PromoIn(sku="SKU-1", was_price=10.00, now_price=9.54))

    assert response == {
        "sku": "SKU-1",
        "discount_pct": 5,
        "was_now_compliant": False,
    }
