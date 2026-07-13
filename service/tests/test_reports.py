"""PPCS-012 — daily violations report builder and governed read endpoint.

The report is *generated* and *pulled*; it is never auto-pushed to an external
dashboard (that would be raw outbound egress outside the operating envelope).
These tests exercise the builder and the read endpoint with no live creds.
"""
from app.main import app, daily_violations_report
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


def test_endpoint_returns_report_json_with_injected_provider():
    # Call the handler directly with an injected provider — no DB, no network.
    result = daily_violations_report(report_date="2026-07-13", provider=_sample)
    assert result["report_date"] == "2026-07-13"
    assert result["total_violations"] == 3
    assert result["violations_by_rule"] == {"was_now": 2, "duration": 2}


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
