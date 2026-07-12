import importlib.util
from pathlib import Path

import pytest

RUNNER = Path(__file__).parents[2] / "ci" / "run_migrations.py"
SPEC = importlib.util.spec_from_file_location("run_migrations", RUNNER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
_apply_files = MODULE._apply_files


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql, params=None):
        if sql.startswith("SELECT checksum"):
            checksum = self.conn.applied.get(params[0])
            self.row = (checksum,) if checksum else None
        elif sql.startswith("INSERT INTO"):
            self.conn.applied[params[0]] = params[1]
        elif sql.startswith("CREATE SCHEMA") or sql.startswith(
            "CREATE TABLE IF NOT EXISTS"
        ):
            return
        else:
            self.conn.executed.append(sql)

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self):
        self.applied = {}
        self.executed = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_applies_once_then_skips(tmp_path: Path):
    migration = tmp_path / "0001_test.sql"
    migration.write_text("CREATE TABLE :schema.example (id int);", encoding="utf-8")
    conn = FakeConnection()

    assert _apply_files(conn, "team01", [str(migration)]) == (1, 0)
    assert conn.executed == ["CREATE TABLE team01.example (id int);"]
    assert _apply_files(conn, "team01", [str(migration)]) == (0, 1)
    assert conn.executed == ["CREATE TABLE team01.example (id int);"]


def test_rejects_changed_applied_migration(tmp_path: Path):
    migration = tmp_path / "0001_test.sql"
    migration.write_text("SELECT 1;", encoding="utf-8")
    conn = FakeConnection()
    _apply_files(conn, "team01", [str(migration)])

    migration.write_text("SELECT 2;", encoding="utf-8")
    with pytest.raises(SystemExit, match="changed after it was applied"):
        _apply_files(conn, "team01", [str(migration)])
    assert conn.rollbacks == 1
