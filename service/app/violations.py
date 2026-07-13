"""Violations state for PPCS-014.

Support teams want a simple `/violations` feed of recent non-compliant
validations without logging into PPCS. This module owns:

- `Violation`: one non-compliant verdict, matching the `/violations` shape in
  api-contract.md (sku, failed rule ids, human-readable reason, ISO-8601
  timestamp).
- `ViolationRepository`: a tiny in-memory abstraction so the endpoint is
  testable without live Lakebase credentials. Per the dispatcher note on the
  ticket, this is intentionally minimal — not a persistence layer. A later
  ticket can swap in a Lakebase-backed implementation behind the same
  `record` / `recent` interface without touching the endpoint.

No promo payloads are logged here (see api-contract.md): rows live in process
memory only and are never emitted to logs or trace metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Violation:
    """One non-compliant validation surfaced by `GET /violations`."""

    sku: str
    rule_ids: list[str]
    reason: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "rule_ids": list(self.rule_ids),
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ViolationRepository:
    """In-memory store of recent non-compliant validations.

    Deliberately small: an ordered list capped to the most recent `max_rows`
    entries. Newest first on read so support teams see the latest violations at
    the top. No database, so tests need no live Lakebase credentials.
    """

    def __init__(self, max_rows: int = 100) -> None:
        self._rows: list[Violation] = []
        self._max_rows = max_rows

    def record(
        self,
        sku: str,
        rule_ids: list[str],
        reason: str,
        timestamp: str | None = None,
    ) -> Violation:
        """Append a violation. `timestamp` is injectable so tests are deterministic."""
        violation = Violation(
            sku=sku,
            rule_ids=list(rule_ids),
            reason=reason,
            timestamp=timestamp or _now_iso(),
        )
        self._rows.append(violation)
        if len(self._rows) > self._max_rows:
            self._rows = self._rows[-self._max_rows :]
        return violation

    def recent(self) -> list[Violation]:
        """Return recorded violations, newest first."""
        return list(reversed(self._rows))

    def clear(self) -> None:
        self._rows.clear()
