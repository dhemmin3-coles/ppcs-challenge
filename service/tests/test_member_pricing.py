"""PPCS-009 — member-only prices must not be advertised as general prices.

The rule (see service/api-contract.md): when ``member_only=true`` and the
``display_channel`` indicates a general public context, the promo is
non-compliant for the member-pricing rule. A public offer is not affected, and
``member_price_compliant`` only appears in the /validate response when the rule
applies — keeping the plain was/now response shape pinned.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.rules import Promo, is_member_price_compliant, is_member_price_rule_applicable


client = TestClient(app)


# --- rule-level -----------------------------------------------------------

def test_member_only_advertised_public_is_non_compliant():
    promo = Promo(
        "A", was_price=10.0, now_price=9.0,
        member_only=True, display_channel="public",
    )
    assert is_member_price_rule_applicable(promo) is True
    assert is_member_price_compliant(promo) is False


def test_member_only_labelled_member_is_compliant():
    promo = Promo(
        "B", was_price=10.0, now_price=9.0,
        member_only=True, display_channel="member",
    )
    assert is_member_price_compliant(promo) is True


def test_public_offer_is_not_governed_by_the_rule():
    promo = Promo(
        "C", was_price=10.0, now_price=9.0,
        member_only=False, display_channel="public",
    )
    assert is_member_price_rule_applicable(promo) is False
    # Not applicable is treated as compliant.
    assert is_member_price_compliant(promo) is True


def test_member_only_without_channel_is_compliant():
    # Nothing claims it is public, so an absent channel does not fail the promo.
    promo = Promo("D", was_price=10.0, now_price=9.0, member_only=True)
    assert is_member_price_compliant(promo) is True


def test_channel_matching_is_case_insensitive():
    promo = Promo(
        "E", was_price=10.0, now_price=9.0,
        member_only=True, display_channel="  PUBLIC ",
    )
    assert is_member_price_compliant(promo) is False


def test_unknown_channel_is_not_treated_as_public():
    promo = Promo(
        "F", was_price=10.0, now_price=9.0,
        member_only=True, display_channel="email-vip",
    )
    assert is_member_price_compliant(promo) is True


# --- API-level ------------------------------------------------------------

def test_api_member_only_public_returns_non_compliant():
    response = client.post(
        "/validate",
        json={
            "sku": "SKU-1", "was_price": 10.0, "now_price": 9.0,
            "member_only": True, "display_channel": "public",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["member_price_compliant"] is False
    # Existing verdict fields are untouched.
    assert body["was_now_compliant"] is True
    assert body["sku"] == "SKU-1"


def test_api_member_only_member_channel_returns_compliant():
    response = client.post(
        "/validate",
        json={
            "sku": "SKU-1", "was_price": 10.0, "now_price": 9.0,
            "member_only": True, "display_channel": "member",
        },
    )
    assert response.status_code == 200
    assert response.json()["member_price_compliant"] is True


def test_api_public_offer_omits_member_field():
    # Public / non-member promo keeps the stable was/now-only response shape.
    response = client.post(
        "/validate",
        json={"sku": "SKU-1", "was_price": 10.0, "now_price": 9.0},
    )
    assert response.status_code == 200
    assert response.json() == {
        "sku": "SKU-1",
        "discount_pct": 10,
        "was_now_compliant": True,
    }
