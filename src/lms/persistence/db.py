"""SQLite connection + transactions.  OWNER: Person 2 (see docs/team/2.md).

Signatures are CONTRACT - implement the bodies, do not rename/re-type.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from lms import config

_db_path: Path = config.DB_PATH


def set_db_path(path: str | Path) -> None:
    """Point the app at another DB file (tests use a tmp_path file)."""
    global _db_path
    _db_path = Path(path)


def get_db_path() -> Path:
    return _db_path


def get_conn() -> sqlite3.Connection:
    """Open a connection to the current DB path.

    Must: create parent dir if missing (_db_path.parent.mkdir(parents=True, exist_ok=True)), set row_factory = sqlite3.Row,
    execute 'PRAGMA foreign_keys = ON', and use isolation_level=None
    (autocommit) so transaction() controls BEGIN/COMMIT explicitly.
    """
    raise NotImplementedError


def init_db(conn: sqlite3.Connection) -> None:
    """Run config.SCHEMA_PATH (idempotent: CREATE ... IF NOT EXISTS)."""
    raise NotImplementedError


def drop_all(conn: sqlite3.Connection) -> None:
    """Drop all tables + triggers (used by seed.reset_db)."""
    raise NotImplementedError


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """`with transaction() as conn:` -> BEGIN IMMEDIATE ... COMMIT, ROLLBACK on any exception.

    BEGIN IMMEDIATE takes the write lock up front so check-then-insert
    (availability check + insert request) is atomic. Always close the connection.
    """
    raise NotImplementedError
    yield  # pragma: no cover
