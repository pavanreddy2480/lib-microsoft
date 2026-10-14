"""Fixtures for the librarian-UI tests (Person 6).

The shared tests/conftest.py has an autouse `fresh_db` that needs the real persistence
layer (still NotImplementedError until P2/P3 land). The librarian-UI unit and e2e tests
use an in-memory port instead, so we override that fixture here; the integration tests
build the real database themselves and skip cleanly while it is not implemented.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from lms.domain import clock
from lms.domain.models import Role, User
from lms.ui.librarian import registry
from .fakes import InMemoryPort

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "app" / "pages"


@pytest.fixture(autouse=True)
def fresh_db():  # overrides tests/conftest.py::fresh_db for this folder
    clock.reset_business_today()
    registry.reset_port()
    yield
    clock.reset_business_today()
    registry.reset_port()


@pytest.fixture
def librarian_user() -> User:
    return User(1, "librarian", "Library Staff", Role.LIBRARIAN)


@pytest.fixture
def member_user() -> User:
    return User(2, "asha", "Asha Rao", Role.MEMBER)


@pytest.fixture
def fake_port() -> InMemoryPort:
    port = InMemoryPort()
    registry.set_port(port)
    return port
