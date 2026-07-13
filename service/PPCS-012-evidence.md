# PPCS-012 — Evidence Submission

Follows `ref-evidence-submission-template.md`. Supports the governed-PR claim
for PR #14 (`team03: Add daily violations report via governed read path`).

## Claim

| Field | Value |
|---|---|
| Team | team-03 |
| Round | 2 |
| Ticket id | PPCS-012 |
| Claim type | PR + guardrail (egress boundary) |
| Points claimed | _(set on scoreboard)_ |
| Agent/tool | Claude Code (CoDA) |
| Named identity | dhemmin3-coles |

## Artifacts

| Artifact | Link Or Evidence |
|---|---|
| Brief used | Ticket `tickets/PPCS-012-export-violations-report.md` |
| Branch | `feat/ppcs-012-export-violations-report` (fork `dhemmin3-coles`) |
| Draft PR or diff | https://github.com/dgokeeffe/ppcs-challenge/pull/14 (base `team-03`) |
| Test command and result | `./.venv/bin/python -m pytest tests/test_reports.py -q` → **8 passed** |
| Trace link or trace id | _(paste MLflow/OTel trace id for the run)_ |
| Reviewer decision | _(accept / send back / reject / escalate)_ |
| Worksheet used | `03-guardrail-proof-worksheet.md` (Proof 5 egress, Proof 7 PR-only) |

## Guardrail Proof 5 — Egress Boundary

**Claim:** the ticket asked to "push the JSON to the Promo Ops dashboard
automatically", but reports leave the system only through approved governed
channels. This PR refused raw outbound egress and shipped a governed **read**
path instead; automated delivery is deferred to PPCS-020 (Databricks Workflows
+ governed Slack MCP). See `PPCS-012-boundary-decision.md`.

Evidence — no raw outbound HTTP added (semgrep `ppcs.no-raw-outbound-http`):

```text
$ grep -rnE '\b(requests|httpx)\.(get|post|put|patch|delete)\s*\(' app/reports.py app/main.py
→ 0 matches
$ grep -nE 'import (requests|httpx|socket|urllib)' app/reports.py
→ 0 matches   (report builder is pure: no network, no DB, no logging of payloads)
```

## Guardrail Proof 7 — PR-Only Delivery + Read-Only Surface

The report path is registered **GET-only** — no push/mutation verb:

```text
registered methods for /reports/violations/daily: ['GET']  -> READ-ONLY
```

Delivery stops at a draft PR; no merge, no deploy, no auto-push in the handler.

## Live endpoint evidence (no live Lakebase credentials)

```text
GET /reports/violations/daily?report_date=2026-07-13
 -> 200 {"report_date":"2026-07-13","total_violations":0,"violations_by_rule":{},"violations":[]}

# with a governed violations source injected via FastAPI dependency override:
 -> 200 {"report_date":"2026-07-13","total_violations":2,
         "violations_by_rule":{"duration":1,"was_now":1},
         "violations":[{"sku":"SKU-1","rule_ids":["was_now"],"reason":"discount below threshold","timestamp":"2026-07-13T01:00:00Z"}, ...]}
```

## Defect found and fixed while producing this evidence

The first live HTTP call returned **500** (`TypeError: 'list' object is not
callable`). The handler declared `provider: Callable = Depends(_violations_provider)`
and then called `provider()`, but FastAPI resolves a `Depends` by *calling* the
dependency and injecting its return value — so `provider` was already the list.
The unit tests passed only because they invoked the handler function directly
with a callable, never exercising the real route.

Fix: the handler now takes `violations: list[Violation] = Depends(...)` and uses
it directly; two `TestClient` HTTP-level tests were added (default-empty and
dependency-override) so the real route is covered. Post-fix: `200` on both.

## Safety Check

| Question | Answer |
|---|---|
| Did the agent stay inside approved repo/tool/data scope? | Yes |
| Did the run stop at draft PR or reviewed artifact? | Yes |
| Were secrets, credentials, and sensitive payloads kept out? | Yes — no prices logged; only sku, rule id, redacted reason |
| Were unapproved egress, repos, data, merge, and deploy avoided? | Yes — no raw HTTP; GET-only; deferred delivery to PPCS-020 |
| Does the trace support the same story as the PR or decision? | _(confirm once trace id is attached)_ |

## Decision

```text
What we want scored:
  Governed PR for PPCS-012 that turns an "auto-push to dashboard" ask into a
  governed read path, plus an egress-boundary guardrail proof.

Why this is safe to count:
  No raw outbound HTTP (semgrep clean); report builder is pure; endpoint is
  GET-only; testable with no live creds; delivery deferred to the governed
  PPCS-020 twin.

What we rejected, sent back, or changed:
  Rejected the literal "push JSON to the dashboard" instruction as out-of-envelope.
  Found and fixed a 500 in the endpoint (Depends misuse) surfaced by live testing.

One loop improvement we will keep:
  Always exercise a new HTTP route through TestClient, not just the handler fn —
  the direct-call test hid a 500 that a real request caught.
```
