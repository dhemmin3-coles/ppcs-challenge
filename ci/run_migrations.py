#!/usr/bin/env python3
"""Apply PPCS SQL migrations to a Lakebase endpoint.

Runs every *.sql file in service/migrations/ in filename order against the
target schema, substituting the literal token `:schema` with the given schema
name. Idempotent (all migrations use IF NOT EXISTS / ON CONFLICT), so it is
safe to re-run against production team schemas or a fresh CI branch clone.

Usage:
    python ci/run_migrations.py --schema team01
    python ci/run_migrations.py --schema ci_pr_1234 --host <h> --target <endpoint>

Connection: mints a fresh OAuth credential the same way the app does
(POST /api/2.0/postgres/credentials), then connects with psycopg. Host and
endpoint target come from flags or the PPCS_LAKEBASE_HOST / PPCS_LAKEBASE_TARGET
env vars that ci/lakebase_branch.py writes into $GITHUB_ENV.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import os
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "service" / "migrations"
DB_NAME = "databricks_postgres"


def _mint_token(endpoint: str) -> str:
    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient()
    cred = client.api_client.do(
        "POST", "/api/2.0/postgres/credentials", body={"endpoint": endpoint}
    )
    return cred["token"]


def _db_user() -> str:
    # In CI the connecting identity is the SP client id; locally fall back to
    # the workspace user name.
    user = os.environ.get("DATABRICKS_CLIENT_ID")
    if user:
        return user
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient().current_user.me().user_name


def _quote_ident(name: str) -> str:
    # schema comes from CI (branch/team name) — still validate defensively.
    if not name.replace("_", "").isalnum():
        raise SystemExit(f"unsafe schema name: {name!r}")
    return name


def _apply_files(conn, schema: str, files: list[str]) -> tuple[int, int]:
    """Apply new migrations atomically and reject changed migration history."""
    applied = 0
    skipped = 0
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS {schema}._ppcs_schema_migrations ("
            "version text PRIMARY KEY, checksum text NOT NULL, "
            "applied_at timestamptz NOT NULL DEFAULT now())"
        )
    conn.commit()

    for path in files:
        version = Path(path).name
        raw_sql = Path(path).read_text(encoding="utf-8")
        checksum = hashlib.sha256(raw_sql.encode()).hexdigest()
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT checksum FROM {schema}._ppcs_schema_migrations "
                "WHERE version = %s",
                (version,),
            )
            row = cur.fetchone()
            if row:
                if row[0] != checksum:
                    conn.rollback()
                    raise SystemExit(
                        f"migration {version} changed after it was applied"
                    )
                print(f"skipping {version} (already applied)", flush=True)
                skipped += 1
                continue

            print(f"applying {version} -> schema {schema}", flush=True)
            cur.execute(raw_sql.replace(":schema", schema))
            cur.execute(
                f"INSERT INTO {schema}._ppcs_schema_migrations "
                "(version, checksum) VALUES (%s, %s)",
                (version, checksum),
            )
        conn.commit()
        applied += 1

    return applied, skipped


def apply_migrations(schema: str, host: str, target: str) -> None:
    import psycopg

    schema = _quote_ident(schema)
    files = sorted(glob.glob(str(MIGRATIONS_DIR / "*.sql")))
    if not files:
        raise SystemExit(f"no migrations found in {MIGRATIONS_DIR}")

    token = _mint_token(target)
    with psycopg.connect(
        host=host,
        dbname=DB_NAME,
        user=_db_user(),
        password=token,
        sslmode="require",
    ) as conn:
        applied, skipped = _apply_files(conn, schema, files)
    print(f"OK: {applied} applied, {skipped} already applied to {schema}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--schema", required=True, help="target Postgres schema")
    ap.add_argument("--host", default=os.environ.get("PPCS_LAKEBASE_HOST"))
    ap.add_argument("--target", default=os.environ.get("PPCS_LAKEBASE_TARGET"))
    args = ap.parse_args()

    if not args.host or not args.target:
        sys.exit(
            "host/target required (flags or PPCS_LAKEBASE_HOST / PPCS_LAKEBASE_TARGET)"
        )
    apply_migrations(args.schema, args.host, args.target)


if __name__ == "__main__":
    main()
