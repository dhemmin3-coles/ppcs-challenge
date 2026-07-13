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
