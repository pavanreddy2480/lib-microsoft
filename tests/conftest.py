"""Shared fixtures. OWNER: Person 7 (see tasks/7.md).

Every test gets a fresh, seeded SQLite file in tmp_path and business date 2026-08-01.
Tests will fail with NotImplementedError until P2/P3/P4 land - that is expected (TDD).
"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lms import clock, db, repo, seed  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    db.set_db_path(tmp_path / "test.db")
    clock.reset_business_today()
    seed.reset_db()
    yield
    clock.reset_business_today()


@pytest.fixture
def conn():
    c = db.get_conn()
    yield c
    c.close()


def _user(username):
    c = db.get_conn()
    try:
        user, _hash = repo.get_user_by_username(c, username)
        return user
    finally:
        c.close()


@pytest.fixture
def librarian():
    return _user("librarian")


@pytest.fixture
def asha():
    return _user("asha")


@pytest.fixture
def ravi():
    return _user("ravi")


@pytest.fixture
def title_id():
    """title_id("Clean Code") -> id"""
    def _lookup(name):
        c = db.get_conn()
        try:
            return next(t.id for t in repo.list_titles(c) if t.title == name)
        finally:
            c.close()
    return _lookup


D = date  # shorthand in tests: D(2026, 8, 5)
