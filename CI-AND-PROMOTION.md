# CI and Promotion — how PPCS gets to production

This is the model behind the CI you'll see run on your pull requests. It's also
a teaching point: how a change moves from your branch to production on a managed
Postgres (Lakebase), and where each database primitive fits.

See **`LAKEBASE-DEPLOYMENTS.md`** for the full diagram (Git → CI → production
branch → team schemas → App deploys).

## One sentence

> **Branch = disposable full-DB clone for automation. Schema + role = durable
> multi-tenant isolation. A connection pooler sits in front of it all.**

## Where your team works

Your team owns a **schema** (`team01` … `team10`) inside the shared
`production` branch's `databricks_postgres` database — not its own branch. Each
team's schema is seeded with the PPCS tables (`app_identity_evidence`,
`ppcs_rule_config`, `ppcs_price_history`). This is the real multi-tenant
pattern: one database, isolation by schema + role. It scales to hundreds of
tenants; a "branch per team" would not (Lakebase caps *live* branches at 10).

## What CI does on every pull request

The **lakebase-ci** job in the PPCS CI workflow:

1. **Cuts an ephemeral branch off `production`** — an instant copy-on-write
   clone of the whole database (all team schemas + data).
2. **Runs the migrations** in `service/migrations/*.sql` against an isolated CI
   schema on that clone. This is the real test: *does my schema change apply
   cleanly on top of production-shaped data?*
3. **Runs integration tests** against the clone — a live, isolated, realistic
   Postgres. Break it all you like; it's a throwaway.
4. **Deletes the branch** — always, even on failure.

## The key idea

You never push a branch's **data** to prod. You push the **migration** you
proved works on a prod-shaped clone. Migrations flow **up**
(your PR → staging → production); production data flows **down** from the
Lakehouse via reverse-ETL. Branches are for *validating change*, not for
carrying data to prod.

```
production (protected, fed from the Lakehouse)
   │  CI branches off it per PR
   ├── ci-pr-123   (ephemeral, migrated, tested, deleted)
   └── ci-pr-124   (ephemeral)
```

## Writing a migration

Add a new numbered file under `service/migrations/`, e.g.
`0003_add_promo_window.sql`. Use `:schema` wherever you'd name the schema —
CI substitutes the target schema (your team schema, or the CI clone's schema):

```sql
ALTER TABLE :schema.ppcs_rule_config
    ADD COLUMN IF NOT EXISTS max_duration_days numeric;
```

Keep migrations idempotent (`IF NOT EXISTS`, `ON CONFLICT`) so they can re-run
safely. CI applies them in filename order and records each filename plus its
SHA-256 checksum in `<schema>._ppcs_schema_migrations`. A rerun skips recorded
migrations; changing a migration after it has been applied fails the run.

## Connecting (no secrets)

The app and CI both mint a short-lived OAuth credential per connection
(`POST /api/2.0/postgres/credentials`) and connect over TLS — no stored
password. See `LAKEBASE.md` for a hands-on connection snippet. Any ticket that
tempts you to hardcode a DB password or reach another team's schema is a trap.
