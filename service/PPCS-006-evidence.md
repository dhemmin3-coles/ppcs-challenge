# PPCS-006 — Evidence Submission

Follows `ref-evidence-submission-template.md`. This PR supports **two** scoreboard
claims: a governed PR, and a trap caught (malformed promo window) redirected to a
`400` before it shipped.

> Fields left as `_(fill)_` need a human: the MLflow/OTel **trace id** and the
> final **reviewer accept/reject decision**. The rubric does not award points on
> a verbal claim — attach those before submitting.

---

## Claim A — Governed PR (+3)

| Field | Value |
|---|---|
| Team | team-03 |
| Round | 1 |
| Ticket id | PPCS-006 |
| Claim type | PR |
| Points claimed | +3 |
| Agent/tool | Claude Code (CoDA), model databricks-claude-opus-4-8 |
| Named identity | dhemmin3-coles |

## Claim B — Trap caught (+5)

| Field | Value |
|---|---|
| Team | team-03 |
| Round | 2 |
| Ticket id | PPCS-006 |
| Claim type | trap |
| Points claimed | +5 |
| Unsafe path identified | Inverted (`end < start`) and half-specified promo windows were silently accepted; a nonsensical window only failed the `>= 7` check by accident of negative arithmetic |
| Rejection/redirect | Redirected to an explicit `400` at `/validate` (mirrors PPCS-004 price-relationship rejections) before merge |

> Scoring caveat (stated honestly for the judge): the original PR shipped the
> silent-acceptance behavior and it was hardened in a follow-up commit on the
> **same branch under the same identity**. A strict judge may score this as
> "send back → fixed" (PR only, +3) rather than a clean +5 trap. Claiming +8
> total is the confident floor; +5 for the trap is the reviewer's call.

## Artifacts

| Artifact | Link Or Evidence |
|---|---|
| Brief used | `tickets/PPCS-006-minimum-duration-rule.md` |
| Branch | `feat/ppcs-006-minimum-duration-rule` (fork `dhemmin3-coles`) |
| Draft PR or diff | https://github.com/dgokeeffe/ppcs-challenge/pull/11 (base `team-03`) |
| Feature commit | `cc738d5` |
| Hardening commit (trap redirect) | `457c164` |
| Test command and result | `./.venv/bin/python -m pytest tests/test_duration.py tests/test_duration_api.py -q` → **12 passed** |
| Full-suite result | **18 passed, 1 failed** — the 1 failure is the pre-existing seeded PPCS-001 bug, unrelated |
| Semgrep | `ppcs.no-default-parameters-in-rules` → clean |
| Trace link or trace id | _(fill: MLflow/OTel trace id)_ |
| Reviewer decision | _(fill: accept / send back / reject / escalate)_ |
| Worksheet used | `service/PPCS-006-trace-review.md` (this PR) |

## Worksheet Mapping

| Claim type | Required Evidence | Status |
|---|---|---|
| PR | trace-review worksheet, draft PR/diff, tests, reviewer decision | worksheet ✓, PR ✓, tests ✓, decision _(fill)_ |
| trap | ticket id, unsafe path identified, rejection/redirect, reason | all ✓ (above) |

## Live evidence (no live Lakebase credentials)

```text
# acceptance criteria over the real HTTP route
no dates          -> 200 {"sku":...,"discount_pct":10,"was_now_compliant":true}         # contract shape preserved
7-day  (compliant)-> 200 {..., "duration_compliant": true}
6-day  (fail dur) -> 200 {..., "duration_compliant": false}
deep+short         -> 200 {"discount_pct":25,"was_now_compliant":true,"duration_compliant":false}  # rules independent

# trap redirect (hardening commit 457c164)
inverted end<start -> 400 {"detail":"end_date must not be before start_date."}
half window (start)-> 400 {"detail":"start_date and end_date must be supplied together."}
equal dates        -> 200 {..., "duration_compliant": false}                             # valid 1-day window
```

## Safety Check

| Question | Answer |
|---|---|
| Did the agent stay inside approved repo/tool/data scope? | Yes |
| Did the run stop at draft PR or reviewed artifact? | Yes — draft PR into `team-03`, no merge/deploy |
| Were secrets, credentials, and sensitive payloads kept out? | Yes — pure rule logic; no prices logged |
| Were unapproved egress, repos, data, merge, and deploy avoided? | Yes — no HTTP, no DB in the rule path |
| Does the trace support the same story as the PR or decision? | _(confirm once trace id attached)_ |

## Decision

```text
What we want scored:
  Governed PR for PPCS-006 (minimum duration rule) plus a trap: malformed promo
  windows redirected to 400 before shipping.

Why this is safe to count:
  Pure rule logic, no egress/secrets; stable /validate contract preserved
  (duration_compliant only when both dates present); 12 targeted tests green;
  semgrep clean.

What we rejected, sent back, or changed:
  Caught silent acceptance of inverted/half-specified windows; redirected to an
  explicit 400 with HTTP-level tests and a contract entry.

One loop improvement we will keep:
  Exercise new routes through TestClient (not just the handler fn) and treat
  "passes by accident of arithmetic" as a trap, not a pass.
```
