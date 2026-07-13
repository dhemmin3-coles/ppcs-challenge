"""Daily violations report (PPCS-012).

Scope note — this module deliberately stops at *generating* the report and
handing it back through a governed read path. It does **not** push the JSON to
an external dashboard. Auto-egress to an unapproved endpoint is outside the PPCS
operating envelope (see 00-operating-envelope-card.md and the
`ppcs.no-raw-outbound-http` semgrep rule); governed scheduled delivery is
PPCS-020's job (Databricks Workflows + the governed Slack MCP). Keeping the
builder pure makes it trivial for that job to reuse without a live database.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Violation:
    """One non-compliant validation, as surfaced by the /violations state.

    Mirrors the `/violations` shape in api-contract.md: sku, the rule ids that
    failed, a human-readable reason, and the verdict timestamp (ISO-8601).
    """

    sku: str
    rule_ids: list[str]
    reason: str
    timestamp: str


@dataclass
class DailyViolationsReport:
    report_date: str
    total_violations: int
    violations_by_rule: dict[str, int]
    violations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "report_date": self.report_date,
            "total_violations": self.total_violations,
            "violations_by_rule": self.violations_by_rule,
            "violations": self.violations,
        }


def build_daily_violations_report(
    violations: list[Violation], report_date: str
) -> DailyViolationsReport:
    """Summarise a day's violations into a report payload.

    Pure and side-effect free: no database, no network, no logging of promo
    payloads. `report_date` is passed in (not read from the clock) so the same
    builder is deterministic in tests and reusable by a scheduled job.
    """
    by_rule: dict[str, int] = {}
    for violation in violations:
        for rule_id in violation.rule_ids:
            by_rule[rule_id] = by_rule.get(rule_id, 0) + 1

    rows = [
        {
            "sku": v.sku,
            "rule_ids": list(v.rule_ids),
            "reason": v.reason,
            "timestamp": v.timestamp,
        }
        for v in violations
    ]

    return DailyViolationsReport(
        report_date=report_date,
        total_violations=len(violations),
        violations_by_rule=dict(sorted(by_rule.items())),
        violations=rows,
    )
