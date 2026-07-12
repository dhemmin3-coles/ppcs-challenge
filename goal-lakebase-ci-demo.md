# Goal: prove a PPCS migration on a production-shaped Lakebase branch

Demonstrate the database delivery loop for PPCS using the existing Lakebase CI
helpers in this repository.

## Outcome

Starting from the Lakebase `production` branch:

1. Create a short-lived copy-on-write branch.
2. Apply the PPCS migrations to an isolated schema on that clone.
3. Run a live read/write smoke test against the migrated clone.
4. Show that the production branch was not mutated by the CI check.
5. Delete the clone, including when a command fails.
6. Stop for human approval. After the Git PR is merged, apply the same reviewed
   migration to production. Do not copy or "merge" clone data into production.

## Operating constraints

- Work only in this repository.
- Use the existing `ci/lakebase_branch.py`, `ci/run_migrations.py`, and
  `ci/lakebase_smoketest.py` helpers; do not create a parallel implementation.
- Use Databricks OAuth/profile authentication. Never print or persist a database
  token, password, or connection string.
- Do not merge a Git PR, deploy the App, or migrate production without an
  explicit human approval at the marked stop.
- Always delete the ephemeral Lakebase branch.

## Live demo

Run from the `ppcs-challenge` repository root. Change the profile if the demo
workspace uses a different Databricks CLI profile.

```bash
export DATABRICKS_CONFIG_PROFILE=lakemeter
export PPCS_PROJECT=projects/ppcs-coda-challenge
export PPCS_SOURCE_BRANCH=production

CI_BRANCH="ci-demo-$(date +%Y%m%d%H%M%S)"
CI_SCHEMA="${CI_BRANCH//-/_}"
cleanup() {
  uv run --project service python ci/lakebase_branch.py delete "$CI_BRANCH"
}
trap cleanup EXIT

# 1. Create a disposable, production-shaped Lakebase branch.
CREATE_OUTPUT="$(uv run --project service python ci/lakebase_branch.py create "$CI_BRANCH" --ttl-seconds 3600)"
PPCS_LAKEBASE_HOST="$(printf '%s\n' "$CREATE_OUTPUT" | sed -n 's/^host=//p')"
export PPCS_LAKEBASE_HOST
export PPCS_LAKEBASE_TARGET="$PPCS_PROJECT/branches/$CI_BRANCH/endpoints/primary"
export PPCS_LAKEBASE_BRANCH="$CI_BRANCH"

printf 'Created %s from %s\n' "$CI_BRANCH" "$PPCS_SOURCE_BRANCH"
databricks api get "/api/2.0/postgres/$PPCS_PROJECT/branches/$CI_BRANCH" \
  | jq '{name, source_branch: .spec.source_branch, ttl: .spec.ttl}'

# 2. Apply every reviewed migration to an isolated schema on the clone.
uv run --project service python ci/run_migrations.py --schema "$CI_SCHEMA"

# 3. Prove the migrated clone supports the PPCS read/write path.
uv run --project service python ci/lakebase_smoketest.py \
  --branch "$CI_BRANCH" \
  --schema "$CI_SCHEMA" \
  --host "$PPCS_LAKEBASE_HOST"

# 4. Run the service tests. PPCS-001's single seeded failure is allowed by the
# repository evaluator; any additional failure blocks promotion.
uv run --project service pytest service/tests -q --junitxml=/tmp/ppcs-demo-junit.xml || true
uv run --project service python ci/evaluate_pytest.py /tmp/ppcs-demo-junit.xml

# 5. Prove the CI-only schema does not exist on production. All migration and
# smoke-test writes above targeted the ephemeral endpoint.
PROD_TARGET="$PPCS_PROJECT/branches/production/endpoints/primary"
databricks psql "$PROD_TARGET" -- \
  -tAc "SELECT to_regnamespace('$CI_SCHEMA') IS NULL AS production_untouched;"

# 6. Delete the clone now; the EXIT trap remains as failure-path protection.
cleanup
trap - EXIT
```

## Human approval and promotion

Pause here and show the evidence: branch name, migration output, smoke-test
`PASS`, and evaluated test result.

After a reviewer approves and merges the **Git PR**, promote the migration by
running it against the production endpoint. Use the durable target schema
chosen for the release (for example `team01`); do not use the ephemeral
`CI_SCHEMA` value.

```bash
PROD_HOST="$(databricks api get "/api/2.0/postgres/$PROD_TARGET" | jq -r '.status.hosts.host')"

# HUMAN APPROVAL REQUIRED BEFORE THIS COMMAND.
uv run --project service python ci/run_migrations.py \
  --schema team01 \
  --host "$PROD_HOST" \
  --target "$PROD_TARGET"
```

## Acceptance evidence

- The ephemeral branch reports `source_branch = production`.
- Migration output ends with `OK: <n> migration(s) applied`.
- The smoke test ends with `PASS` for the ephemeral branch/schema.
- The PPCS test evaluator accepts the result.
- The ephemeral branch no longer exists after the demo.
- Production migration occurs only after the reviewed Git change is merged and
  a human explicitly approves the production command.
