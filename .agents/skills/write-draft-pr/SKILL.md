---
name: write-draft-pr
description: Prepare and open consistent participant-safe draft pull requests for the PPCS challenge. Use when a team asks to write, create, open, or tidy a PR; finish a PPCS ticket; submit work for review; or fix team attribution on a PR. Handles GitHub CLI authentication, team branch naming, verification evidence, a standard PR body, and draft-only creation.
---

# Write a PPCS draft PR

Keep code changes inside this repo and its operating envelope. A temporary PR
body under `/tmp` is allowed but must never be committed. Never merge, deploy,
push to `main`, broaden access, or include secrets or facilitator-only material.

## 1. Establish the work order

1. Read `.agents/instructions.md` and the relevant `tickets/PPCS-NNN-*.md`.
2. Inspect `git status --short`, the current branch, the diff, and recent commits.
3. Identify the team number and ticket ID. Do not guess either one.
4. Use branch `team-NN/PPCS-NNN-short-slug`, based on `team-NN`.

Fetch the team base read-only before creating a missing feature branch:

```bash
git fetch origin team-NN
git switch -c team-NN/PPCS-NNN-short-slug origin/team-NN
```

If the feature branch already exists or has diverged, inspect it and stop for
direction. Do not force-push, reset, or rebase it implicitly.

If the current branch has no `team-NN` identity, stop and ask for the team
number before pushing. This branch token is how the leaderboard associates the
PR with a team.

## 2. Verify GitHub access

Run:

```bash
gh auth status --hostname github.com
gh repo view --json nameWithOwner
```

If authentication is missing or expired, tell the participant that GitHub will
show a browser/device login and get their confirmation before running:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

Then rerun `gh auth status`. Never request, print, paste, or store a token.

## 3. Build the evidence packet

Before opening the PR:

- confirm the diff is limited to the ticket;
- run the ticket's named acceptance test when present;
- run `cd service && uv run pytest -q` and use `.agents/instructions.md` as the
  only authority for classifying an intentional seed failure;
- run relevant static or migration checks when the changed files require them;
- capture the exact commands and outcomes;
- include a trace or run ID when available;
- state what still needs human judgement.

Do not describe “tests passed” without naming the command and result. Do not
claim approval from CI, an agent, or this skill.

If ticket work is still uncommitted, show the exact files that would be staged
and get participant confirmation before creating a ticket-scoped conventional
commit. Preserve unrelated changes and untracked files. Never silently include
`.cursor/`, generated files, environment files, or unrelated lockfile changes.

## 4. Write the PR consistently

Use title:

```text
PPCS-NNN: concise outcome
```

Use this body:

```markdown
## Goal

<Ticket intent and acceptance criterion>

## What changed

- <small, concrete change>
- <small, concrete change>

## Evidence

- Acceptance: `<command>` — <result>
- Regression: `<command>` — <result>
- Trace/run: <link or ID, or “not captured”>

## Scope and safety

- Approved paths changed: <paths>
- Out of scope: <explicit exclusions>
- No merge, deploy, secrets, ungranted data, raw egress, or sensitive telemetry

## Human review

- Decision requested: accept / send back / reject / escalate
- Reviewer should inspect: <correctness, trajectory, guardrail, or runtime concern>
```

Keep the body factual and linkable. The summary is not evidence.

## 5. Open and verify the draft

Push only the feature branch, prepare the body in a temporary file outside the
repo, and check for an existing PR first:

```bash
gh pr list --head team-NN/PPCS-NNN-short-slug \
  --json url,isDraft,title,baseRefName,headRefName
```

If a PR exists, update or report it instead of creating a duplicate. Otherwise
run:

```bash
git push -u origin team-NN/PPCS-NNN-short-slug
gh pr create --draft \
  --base team-NN \
  --head team-NN/PPCS-NNN-short-slug \
  --title "PPCS-NNN: concise outcome" \
  --body-file /tmp/ppcs-pr-body.md
```

Verify the result:

```bash
gh pr view --json url,isDraft,title,baseRefName,headRefName
```

Completion requires `isDraft: true`, base exactly `team-NN`, and head exactly
`team-NN/PPCS-NNN-short-slug`. Return the PR URL, verification results, known
gaps, and the explicit human decision still required.
