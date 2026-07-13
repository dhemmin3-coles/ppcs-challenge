from app.main import PromoIn, validate


def test_validate_returns_existing_verdict_shape():
    response = validate(PromoIn(sku="SKU-OK", was_price=10.00, now_price=9.00))

    assert response == {
        "sku": "SKU-OK",
        "discount_pct": 10.0,
        "was_now_compliant": True,
    }


def test_validate_marginal_discount_rejected_after_ppcs_001_fix():
    # 4.6% markdown must FAIL the 5% genuine-discount bar (PPCS-001 fix).
    response = validate(PromoIn(sku="SKU-1", was_price=10.00, now_price=9.54))

    assert response == {
        "sku": "SKU-1",
        "discount_pct": 4.6,
        "was_now_compliant": False,
    }
