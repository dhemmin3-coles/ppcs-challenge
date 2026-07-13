# Trace Review Worksheet — PPCS-006 (PR #11)

Filled from `02-trace-review-worksheet.md`. `_(fill)_` fields need the human:
the MLflow/OTel trace id and the final accept/reject decision.

## 1. Identify The Run

| Field | Value |
|---|---|
| Team | team-03 |
| Ticket id | PPCS-006 |
| Brief id or brief link | `tickets/PPCS-006-minimum-duration-rule.md` |
| Agent | Claude Code (CoDA) |
| Model | databricks-claude-opus-4-8 |
| Trigger type | Manual |
| Named identity | dhemmin3-coles |
| Operating envelope | PPCS repo; no egress; PR-only into `team-03` |
| Trace link or artifact | _(fill: MLflow/OTel trace id)_ |

## 2. Match Trace To PR

| Evidence | Value | Pass? |
|---|---|---|
| Draft PR link or diff link appears in trace | PR #11 | _(fill)_ |
| Branch or changed files match the PR | `feat/ppcs-006-minimum-duration-rule`; rules.py, main.py, api-contract.md, 2 test files | Yes |
| Test command appears in trace | `pytest tests/test_duration*.py -q` | _(fill)_ |
| test output/result matches the PR claim | 12 passed | Yes |
| Reviewer sub-agent or human review decision appears | Review comment on PR #11 | Yes (comment); human decision _(fill)_ |
| Reviewer finding references diff, tests, scope, safety, and trace | Yes — review covers all | Yes |

## 2a. Evaluation Checks

| Evaluation Mechanism | What It Proves | Evidence | Pass? |
|---|---|---|---|
| Targeted tests | Behavior matches acceptance criteria | `test_duration.py` + `test_duration_api.py`, 12 passed | Yes |
| Semgrep/static check | Code-shape risks absent | `ppcs.no-default-parameters-in-rules` clean | Yes |
| Trace trajectory review | Approved tools/identity/scope, stop at PR | _(confirm against trace id)_ | _(fill)_ |
| Reviewer rubric | Senior engineer accepts correctness/scope/policy | Review comment recommends accept | Yes |

## 3. Inspect Tool Calls

| Tool Call | Target | Result | In Envelope? |
|---|---|---|---|
| repo read/edit | `service/app/rules.py`, `service/app/main.py` | allowed | Yes |
| tests | `pytest` in `.venv` | allowed / 12 passed | Yes |
| git push | fork `dhemmin3-coles` branch | allowed | Yes |
| merge/deploy | — | not attempted | Yes |

## 4. Check Data And Telemetry Safety

| Question | Evidence | Pass? |
|---|---|---|
| Trace avoids raw promo/customer/member payloads? | Rule logic is pure; no logging of prices | Yes |
| Sensitive fields redacted or absent downstream? | No telemetry writes in this path | Yes |
| Prompts, credentials, tokens, connection strings absent? | None added | Yes |
| Telemetry fields useful without being excessive? | n/a for this diff | n/a |

## 5. Review Cost And Context

| Signal | Value | Interpretation |
|---|---:|---|
| Files touched | 6 (incl. evidence) | small, focused diff |
| Number of tool calls | _(fill from trace)_ | |
| Estimated cost | _(fill from trace)_ | |

## 6. Decide

| Decision | When To Use |
|---|---|
| Accept | Trace, diff, tests, review align; no envelope violation. |

```text
Recommended: Accept (human to confirm)

Reason:
  Feature meets all PPCS-006 acceptance criteria; inclusive-counting trap handled
  correctly; stable /validate contract preserved; malformed-window trap caught and
  redirected to 400 with tests. Only the seeded PPCS-001 failure remains, unrelated.

Reviewer sub-agent finding, if used:
  See PR #11 review comment — validation table, two findings, hardening commit 457c164.

Evidence:
  PR https://github.com/dgokeeffe/ppcs-challenge/pull/11 ; commits cc738d5, 457c164 ;
  service/PPCS-006-evidence.md ; 12 passed.

Next brief or guardrail change:
  Consider a semgrep/lint rule for "date arithmetic without inclusive +1 and range guard".
```

## 7. Minimum Trace Bar

Ticket id ✓ · agent+model ✓ · identity ✓ · approved scope ✓ · tool calls+results ✓ ·
test command+outcome ✓ · draft PR ✓ · reviewer decision _(fill)_ · cost signal _(fill)_.
Trace id is the remaining gap to clear the minimum bar for scoring.
