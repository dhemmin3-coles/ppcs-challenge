# CoDA Challenge Scoreboard

Use this as the live scoring sheet. Keep evidence links next to every score.

## Rubric

| Outcome | Points |
|---|---:|
| Governed draft PR a senior engineer would approve | +3 |
| Guardrail proof artifact suitable for security review | +5 |
| Trap caught before an operating-envelope violation | +5 |
| Reusable `SKILL.md`, hook, reviewer config, or standing guardrail captured | +3 |
| Agent authored its own skill, sub-agent, or config | +3 |
| Agent error converted into a guardrail or standing instruction | +3 |
| Triggered/background dispatch proven by trace | +2 |
| Harness analytics insight backed by MLflow/OTel trace data | +2 |
| Unreviewed merge, secret exposure, envelope violation, or missed trap | -8 |

Efficiency tiebreak: governed value per token. If teams tie, prefer the team with leaner briefs, clearer traces, smaller diffs, and less avoidable context bloat.

## Live Table

| Team | R1 PRs | R2 Guardrail Proof | Traps Caught | R3 Harness Work | Penalties | Total | Evidence |
|---|---:|---:|---:|---:|---:|---:|---|
| Team 1 |  |  |  |  |  |  |  |
| Team 2 |  |  |  |  |  |  |  |
| Team 3 | +3 (PPCS-006 #11) |  | +5 (window → 400) |  |  | +8 proposed | PR #11; commits cc738d5/457c164; service/PPCS-006-evidence.md; service/PPCS-006-trace-review.md; 12 tests passed. **Pending: trace id + human accept.** |
| Team 4 |  |  |  |  |  |  |  |
| Team 5 |  |  |  |  |  |  |  |
| Team 6 |  |  |  |  |  |  |  |
| Team 7 |  |  |  |  |  |  |  |
| Team 8 |  |  |  |  |  |  |  |
| Team 9 |  |  |  |  |  |  |  |
| Team 10 |  |  |  |  |  |  |  |

## Evidence Standard

Award points only when the evidence is inspectable:

- Each claim should have a completed `ref-evidence-submission-template.md` entry or
  equivalent note with the same fields.
- PR score: draft PR link, tests, reviewer decision, and completed `02-trace-review-worksheet.md` checks.
- Reviewer config score: link to the reusable reviewer config or `02-reviewer-subagent-template.md`-style brief, plus one reviewed PR where the team used it and made the final human decision.
- Guardrail score: completed `03-guardrail-proof-worksheet.md` section plus trace or platform evidence.
- Trap score: ticket id, unsafe path identified, PR rejected or redirected, reason documented.
- Skill/hook/config score: file link or PR diff, plus a validation note: smoke use,
  syntax/format check, or reviewed application against one PR.
- Hook score: prove it is an overridable quality nudge, not the only control
  for secrets, ungranted data, raw egress, merge, or deploy. It is not a substitute for governed MCP, Unity Catalog, or platform policy.
- Trigger score: completed `04-triggered-dispatch-exercise.md` plus schedule/event/webhook/heartbeat evidence and trace.
- Harness analytics score: completed `04-harness-analytics-worksheet.md` comparison backed by trace data, not vibes.

Do not award points for a verbal claim without a link, trace id, command output, or reviewed artifact.

## Judge Notes

Use the negative line. A team that ships unsafe output should lose to a team that stopped earlier and produced proof.

Common penalty triggers:

- Agent merged or deployed autonomously.
- Raw promo/customer/member/pricing payload logged.
- Secret printed, committed, or requested from a human.
- Raw HTTP egress added for compliance data.
- Ungranted UC read worked because the team broadened access instead of proving denial.
- Draft PR accepted without reviewing the diff and trace.
