import pytest

from app.main import PromoIn, validate
from app.rules import MultiBuy, effective_unit_price


def test_three_for_ten_returns_effective_unit_price():
    # 3 for $10.00 -> 3.33 with normal currency rounding.
    assert effective_unit_price(MultiBuy(quantity=3, bundle_price=10.00)) == 3.33


def test_even_split_unit_price():
    assert effective_unit_price(MultiBuy(quantity=2, bundle_price=5.00)) == 2.50


@pytest.mark.parametrize("quantity", [0, -1])
def test_invalid_quantity_rejected(quantity):
    with pytest.raises(ValueError):
        effective_unit_price(MultiBuy(quantity=quantity, bundle_price=10.00))


@pytest.mark.parametrize("bundle_price", [0.0, -5.00])
def test_invalid_bundle_price_rejected(bundle_price):
    with pytest.raises(ValueError):
        effective_unit_price(MultiBuy(quantity=3, bundle_price=bundle_price))


def test_validate_includes_effective_unit_price_for_multibuy():
    response = validate(
        PromoIn(
            sku="MB-1",
            was_price=10.00,
            now_price=9.00,
            multi_buy={"quantity": 3, "bundle_price": 10.00},
        )
    )
    assert response == {
        "sku": "MB-1",
        "discount_pct": 10,
        "was_now_compliant": True,
        "effective_unit_price": 3.33,
    }


def test_validate_omits_effective_unit_price_without_multibuy():
    # Existing Was/Now shape is unchanged when no multi-buy offer is supplied.
    response = validate(PromoIn(sku="MB-2", was_price=10.00, now_price=9.00))
    assert response == {
        "sku": "MB-2",
        "discount_pct": 10,
        "was_now_compliant": True,
    }
