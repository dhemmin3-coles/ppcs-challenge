"""PPCS-012 — daily violations report builder and governed read endpoint.

The report is *generated* and *pulled*; it is never auto-pushed to an external
dashboard (that would be raw outbound egress outside the operating envelope).
These tests exercise the builder and the read endpoint with no live creds.
"""
from fastapi.testclient import TestClient

from app.main import app, _violations_provider, daily_violations_report
from app.reports import Violation, build_daily_violations_report


def _sample() -> list[Violation]:
    return [
        Violation("SKU-1", ["was_now"], "discount below threshold", "2026-07-13T01:00:00Z"),
        Violation("SKU-2", ["duration"], "runs fewer than 7 days", "2026-07-13T02:00:00Z"),
        Violation(
            "SKU-3",
            ["was_now", "duration"],
            "shallow discount and too short",
            "2026-07-13T03:00:00Z",
        ),
    ]


def test_report_counts_total_violations():
    report = build_daily_violations_report(_sample(), "2026-07-13")
    assert report.report_date == "2026-07-13"
    assert report.total_violations == 3


def test_report_groups_by_rule_id():
    report = build_daily_violations_report(_sample(), "2026-07-13")
    # SKU-3 fails both rules, so it counts toward each bucket.
    assert report.violations_by_rule == {"was_now": 2, "duration": 2}


def test_report_is_empty_when_no_violations():
    report = build_daily_violations_report([], "2026-07-13")
    assert report.total_violations == 0
    assert report.violations_by_rule == {}
    assert report.violations == []


def test_report_rows_preserve_contract_fields():
    report = build_daily_violations_report(_sample(), "2026-07-13")
    first = report.violations[0]
    assert set(first) == {"sku", "rule_ids", "reason", "timestamp"}
    assert first["sku"] == "SKU-1"
    assert first["rule_ids"] == ["was_now"]


def test_endpoint_returns_report_json_with_injected_violations():
    # Call the handler directly with an injected (already-resolved) list — the
    # dependency yields the list, so the handler receives a list, not a callable.
    result = daily_violations_report(report_date="2026-07-13", violations=_sample())
    assert result["report_date"] == "2026-07-13"
    assert result["total_violations"] == 3
    assert result["violations_by_rule"] == {"was_now": 2, "duration": 2}


def test_endpoint_serves_report_over_http_default_empty():
    # Exercise the real HTTP route (not just the handler fn). The default
    # provider yields an empty list, so this must be 200 with an empty report —
    # no live Lakebase credentials required.
    client = TestClient(app)
    response = client.get("/reports/violations/daily", params={"report_date": "2026-07-13"})
    assert response.status_code == 200
    body = response.json()
    assert body["report_date"] == "2026-07-13"
    assert body["total_violations"] == 0
    assert body["violations"] == []


def test_endpoint_serves_report_over_http_with_dependency_override():
    # Override the violations source the way a governed job would, and drive the
    # real route end-to-end.
    client = TestClient(app)
    app.dependency_overrides[_violations_provider] = _sample
    try:
        response = client.get(
            "/reports/violations/daily", params={"report_date": "2026-07-13"}
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["total_violations"] == 3
    assert body["violations_by_rule"] == {"was_now": 2, "duration": 2}
    assert set(body["violations"][0]) == {"sku", "rule_ids", "reason", "timestamp"}


def test_endpoint_registered_as_get_only():
    routes = {
        r.path: r.methods
        for r in app.routes
        if getattr(r, "path", None) == "/reports/violations/daily"
    }
    assert routes, "daily report route should be registered"
    methods = routes["/reports/violations/daily"]
    assert "GET" in methods
    # Read-only: no push/mutation verbs on the report path.
    assert "POST" not in methods and "PUT" not in methods
