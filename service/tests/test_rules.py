from app.rules import Promo, is_was_now_compliant


def test_genuine_discount_passes():
    # 10% markdown — clearly compliant.
    assert is_was_now_compliant(Promo("A", was_price=10.00, now_price=9.00)) is True


def test_deep_discount_passes():
    assert is_was_now_compliant(Promo("C", was_price=20.00, now_price=15.00)) is True


def test_marginal_discount_below_threshold_fails():
    # 4.6% markdown must FAIL the 5% genuine-discount bar.
    assert is_was_now_compliant(Promo("B", was_price=10.00, now_price=9.54)) is False


def test_exact_five_percent_discount_passes():
    assert is_was_now_compliant(Promo("D", was_price=10.00, now_price=9.50)) is True
