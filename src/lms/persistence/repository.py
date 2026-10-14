"""Data access - plain SQL, no business rules.  OWNER: Person 2 (see docs/team/2.md).

Every function takes an open `conn` as first argument (services pass the
transaction's connection). Convert rows to the dataclasses in models.py:
- dates: date.fromisoformat(row["start_date"])
- enums: RequestStatus(row["status"]), CopyStatus(...), Role(...)
Return None (not raise) when a single row is not found.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import Iterable

from lms.domain.models import (
    ACTIVE_STATUSES, Copy, CopyStatus, Event, Request, RequestStatus, Role, Title, User,
)


def now_ts() -> str:
    """Wall-clock timestamp 'YYYY-MM-DD HH:MM:SS' for created_at / issued_at / events."""
    raise NotImplementedError


# ---------- users ----------
def insert_user(conn: sqlite3.Connection, username: str, password_hash: str,
                full_name: str, role: str) -> int:
    raise NotImplementedError


def get_user(conn: sqlite3.Connection, user_id: int) -> User | None:
    raise NotImplementedError


def get_user_by_username(conn: sqlite3.Connection, username: str) -> tuple[User, str] | None:
    """Returns (User, password_hash) or None."""
    raise NotImplementedError


def list_members(conn: sqlite3.Connection) -> list[User]:
    raise NotImplementedError


# ---------- titles / copies ----------
def insert_title(conn: sqlite3.Connection, title: str, category: str) -> int:
    raise NotImplementedError


def insert_copy(conn: sqlite3.Connection, title_id: int, copy_code: str,
                status: CopyStatus = CopyStatus.IN_SERVICE, note: str = "") -> int:
    raise NotImplementedError


def list_titles(conn: sqlite3.Connection) -> list[Title]:
    raise NotImplementedError


def get_title(conn: sqlite3.Connection, title_id: int) -> Title | None:
    raise NotImplementedError


def list_copies(conn: sqlite3.Connection, title_id: int | None = None) -> list[Copy]:
    """All copies (optionally for one title), ordered by copy_code."""
    raise NotImplementedError


def get_copy(conn: sqlite3.Connection, copy_id: int) -> Copy | None:
    raise NotImplementedError


def update_copy_status(conn: sqlite3.Connection, copy_id: int, status: CopyStatus,
                       note: str = "") -> None:
    raise NotImplementedError


# ---------- requests ----------
def insert_request(conn: sqlite3.Connection, member_id: int, title_id: int, copy_id: int,
                   start: date, end: date, status: RequestStatus) -> int:
    """Insert with created_at = now_ts(). The DB trigger may raise
    sqlite3.IntegrityError('COPY_OVERLAP') - let it propagate."""
    raise NotImplementedError


def get_request(conn: sqlite3.Connection, request_id: int) -> Request | None:
    raise NotImplementedError


def list_requests(conn: sqlite3.Connection, member_id: int | None = None,
                  statuses: Iterable[RequestStatus] | None = None,
                  title_id: int | None = None) -> list[Request]:
    """Filtered list, newest first (ORDER BY id DESC)."""
    raise NotImplementedError


def update_request_status(conn: sqlite3.Connection, request_id: int, status: RequestStatus,
                          decision_note: str | None = None,
                          issued_at: str | None = None,
                          returned_at: str | None = None) -> None:
    """Update status; only overwrite the optional columns that are not None."""
    raise NotImplementedError


def update_request_copy(conn: sqlite3.Connection, request_id: int, new_copy_id: int) -> None:
    """Used only by the reallocation policy (copy went out of service)."""
    raise NotImplementedError


def active_commitments_for_copy(conn: sqlite3.Connection, copy_id: int) -> list[Request]:
    """Requests on this copy with status in ACTIVE_STATUSES."""
    raise NotImplementedError


def active_commitments_for_title(conn: sqlite3.Connection, title_id: int) -> list[Request]:
    """Requests for this title with status in ACTIVE_STATUSES."""
    raise NotImplementedError


# ---------- audit ----------
def insert_event(conn: sqlite3.Connection, request_id: int, from_status: str | None,
                 to_status: str, actor: str, note: str = "") -> int:
    raise NotImplementedError


def list_events(conn: sqlite3.Connection, request_id: int) -> list[Event]:
    """Oldest first."""
    raise NotImplementedError
