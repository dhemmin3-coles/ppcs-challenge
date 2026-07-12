#!/usr/bin/env python3
"""Lakebase ephemeral-branch lifecycle for CI.

Used by the GitHub Actions pipeline to give each pull request an isolated,
prod-shaped database: branch off `production` (copy-on-write clone), run
migrations + tests against it, then tear it down. This is the workshop's
"getting to prod" demo, running for real on every PR.

Subcommands:
    create   Create an ephemeral branch + RW endpoint off production.
             Prints `host=<h>\\nbranch=<name>` to stdout and, if --github-env
             is set, appends PPCS_LAKEBASE_HOST / PPCS_LAKEBASE_TARGET /
             PPCS_LAKEBASE_BRANCH to $GITHUB_ENV.
    token    Mint a fresh OAuth DB credential for the branch endpoint (stdout).
    delete   Delete the ephemeral branch (idempotent — never fails the build).

Auth: uses databricks-sdk WorkspaceClient (env-configured in CI:
DATABRICKS_HOST + DATABRICKS_CLIENT_ID/SECRET, or a token).

Env:
    PPCS_PROJECT   Lakebase project resource (default projects/ppcs-coda-challenge)
    PPCS_SOURCE_BRANCH  branch to clone from (default production)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

PROJECT = os.environ.get("PPCS_PROJECT", "projects/ppcs-coda-challenge")
SOURCE = os.environ.get("PPCS_SOURCE_BRANCH", "production")
DB_NAME = "databricks_postgres"


def _client():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


# Resource identifiers used in request bodies / env (no API prefix).
def _branch_path(name: str) -> str:
    return f"{PROJECT}/branches/{name}"


def _endpoint_path(name: str) -> str:
    return f"{_branch_path(name)}/endpoints/primary"


# REST URLs for the beta Postgres surface. The branch/endpoint routes live
# under /api/2.0/postgres/ — without that prefix the workspace returns
# 404 "No API found". (The credentials mint path already includes it.)
def _branches_url() -> str:
    return f"/api/2.0/postgres/{PROJECT}/branches"


def _branch_url(name: str) -> str:
    return f"/api/2.0/postgres/{_branch_path(name)}"


def _endpoints_url(name: str) -> str:
    return f"{_branch_url(name)}/endpoints"


def _endpoint_url(name: str) -> str:
    return f"/api/2.0/postgres/{_endpoint_path(name)}"


def _do(
    client,
    method: str,
    path: str,
    body: dict | None = None,
    query: dict | None = None,
) -> dict:
    return client.api_client.do(method, path, body=body or {}, query=query)


def create(name: str, ttl_seconds: int, github_env: str | None) -> None:
    client = _client()

    # Branch: copy-on-write clone of the source branch at current state.
    _do(
        client,
        "POST",
        _branches_url(),
        {
            "spec": {
                "source_branch": _branch_path(SOURCE),
                "ttl": f"{ttl_seconds}s",
            },
        },
        {"branch_id": name},
    )

    # RW autoscaling endpoint on the new branch.
    try:
        _do(
            client,
            "POST",
            _endpoints_url(name),
            {
                "spec": {
                    "endpoint_type": "ENDPOINT_TYPE_READ_WRITE",
                    "autoscaling_limit_min_cu": 0.5,
                    "autoscaling_limit_max_cu": 4,
                    "suspend_timeout_duration": "300s",
                },
            },
            {"endpoint_id": "primary"},
        )
    except Exception as exc:
        # Newer Lakebase API versions auto-create the primary RW endpoint with
        # the branch; older versions require the explicit call above.
        if "endpoint already exists" not in str(exc).lower():
            raise

    host = _wait_for_host(client, name)

    print(f"host={host}")
    print(f"branch={name}")

    if github_env:
        with open(github_env, "a", encoding="utf-8") as fh:
            fh.write(f"PPCS_LAKEBASE_HOST={host}\n")
            fh.write(f"PPCS_LAKEBASE_TARGET={_endpoint_path(name)}\n")
            fh.write(f"PPCS_LAKEBASE_BRANCH={name}\n")


def _wait_for_host(client, name: str, timeout: int = 180) -> str:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        ep = _do(client, "GET", _endpoint_url(name))
        host = (ep.get("status") or {}).get("hosts", {}).get("host")
        if host:
            return host
        last = ep.get("status", {}).get("current_state")
        time.sleep(5)
    raise SystemExit(f"endpoint host not ready after {timeout}s (state={last})")


def token(name: str) -> None:
    client = _client()
    cred = _do(
        client,
        "POST",
        "/api/2.0/postgres/credentials",
        {"endpoint": _endpoint_path(name)},
    )
    sys.stdout.write(cred["token"])


def delete(name: str) -> None:
    # Idempotent: teardown must never fail the build.
    try:
        client = _client()
        _do(client, "DELETE", _branch_url(name))
        print(f"deleted branch {name}")
    except Exception as exc:  # noqa: BLE001 - best-effort cleanup
        print(f"warning: delete of {name} failed (ignored): {exc}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create")
    c.add_argument("name")
    c.add_argument("--ttl-seconds", type=int, default=7200)
    c.add_argument("--github-env", default=os.environ.get("GITHUB_ENV"))

    t = sub.add_parser("token")
    t.add_argument("name")

    d = sub.add_parser("delete")
    d.add_argument("name")

    args = ap.parse_args()
    if args.cmd == "create":
        create(args.name, args.ttl_seconds, args.github_env)
    elif args.cmd == "token":
        token(args.name)
    elif args.cmd == "delete":
        delete(args.name)


if __name__ == "__main__":
    main()
