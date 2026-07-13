"""PPCS-014 — /violations endpoint and its in-memory repository.

Exercises the repository abstraction and the endpoint with no live Lakebase
credentials: violations are recorded in process memory by /validate and read
back, newest first, via /violations.
"""
from fastapi.testclient import TestClient

from app.main import app, violation_repo
from app.violations import ViolationRepository


client = TestClient(app)


def setup_function(_func):
    # Each test starts from a clean, isolated violations store.
    violation_repo.clear()


# --- repository abstraction -------------------------------------------------

def test_repository_records_and_reads_newest_first():
    repo = ViolationRepository()
    repo.record("SKU-1", ["was_now"], "shallow discount", "2026-07-13T01:00:00Z")
    repo.record("SKU-2", ["was_now"], "shallow discount", "2026-07-13T02:00:00Z")

    rows = repo.recent()
    assert [r.sku for r in rows] == ["SKU-2", "SKU-1"]


def test_repository_starts_empty():
    assert ViolationRepository().recent() == []


def test_repository_caps_to_max_rows():
    repo = ViolationRepository(max_rows=2)
    for i in range(5):
        repo.record(f"SKU-{i}", ["was_now"], "shallow discount", f"2026-07-13T0{i}:00:00Z")

    rows = repo.recent()
    assert len(rows) == 2
    # Only the two most recent survive, newest first.
    assert [r.sku for r in rows] == ["SKU-4", "SKU-3"]


def test_violation_to_dict_matches_contract_fields():
    v = ViolationRepository().record(
        "SKU-1", ["was_now"], "shallow discount", "2026-07-13T01:00:00Z"
    )
    assert set(v.to_dict()) == {"sku", "rule_ids", "reason", "timestamp"}


# --- endpoint ---------------------------------------------------------------

def test_violations_endpoint_empty_by_default():
    response = client.get("/violations")
    assert response.status_code == 200
    assert response.json() == []


def test_only_non_compliant_validations_are_returned():
    # Non-compliant: 1% markdown is below the 5% genuine-discount bar.
    client.post("/validate", json={"sku": "SKU-BAD", "was_price": 10.0, "now_price": 9.9})
    # Compliant: 20% markdown clears the bar and must NOT appear.
    client.post("/validate", json={"sku": "SKU-OK", "was_price": 10.0, "now_price": 8.0})

    body = client.get("/violations").json()
    skus = [row["sku"] for row in body]
    assert "SKU-BAD" in skus
    assert "SKU-OK" not in skus


def test_violation_rows_include_required_fields():
    client.post("/validate", json={"sku": "SKU-BAD", "was_price": 10.0, "now_price": 9.9})

    row = client.get("/violations").json()[0]
    assert set(row) == {"sku", "rule_ids", "reason", "timestamp"}
    assert row["sku"] == "SKU-BAD"
    assert row["rule_ids"] == ["was_now"]
    assert isinstance(row["reason"], str) and row["reason"]
    assert isinstance(row["timestamp"], str) and row["timestamp"]


def test_violations_endpoint_is_get_only():
    routes = {
        r.path: r.methods
        for r in app.routes
        if getattr(r, "path", None) == "/violations"
    }
    assert routes, "/violations route should be registered"
    methods = routes["/violations"]
    assert "GET" in methods
    assert "POST" not in methods and "PUT" not in methods
