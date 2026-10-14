"""Data access - plain SQL, no business rules.  OWNER: Person 2 (see docs/team/2.md).

Every function takes an open `conn` as first argument (services pass the
transaction's connection). Convert rows to the dataclasses in models.py:
- dates: date.fromisoformat(row["start_date"])
- enums: RequestStatus(row["status"]), CopyStatus(...), Role(...)
Return None (not raise) when a single row is not found.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Iterable

from lms.domain.models import (
    ACTIVE_STATUSES, Copy, CopyStatus, Event, Request, RequestStatus, Role, Title, User,
)


def now_ts() -> str:
    """Wall-clock timestamp 'YYYY-MM-DD HH:MM:SS' for created_at / issued_at / events."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- row -> dataclass helpers ----------
def _to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        full_name=row["full_name"],
        role=Role(row["role"]),
    )


def _to_title(row: sqlite3.Row) -> Title:
    return Title(id=row["id"], title=row["title"], category=row["category"])


def _to_copy(row: sqlite3.Row) -> Copy:
    return Copy(
        id=row["id"],
        title_id=row["title_id"],
        copy_code=row["copy_code"],
        status=CopyStatus(row["status"]),
        note=row["note"],
    )


def _to_request(row: sqlite3.Row) -> Request:
    return Request(
        id=row["id"],
        member_id=row["member_id"],
        title_id=row["title_id"],
        copy_id=row["copy_id"],
        start_date=date.fromisoformat(row["start_date"]),
        end_date=date.fromisoformat(row["end_date"]),
        status=RequestStatus(row["status"]),
        created_at=row["created_at"],
        decision_note=row["decision_note"],
        issued_at=row["issued_at"],
        returned_at=row["returned_at"],
    )


def _to_event(row: sqlite3.Row) -> Event:
    return Event(
        id=row["id"],
        request_id=row["request_id"],
        from_status=row["from_status"],
        to_status=row["to_status"],
        actor=row["actor"],
        note=row["note"],
        at=row["at"],
    )


_ACTIVE_VALUES = [s.value for s in ACTIVE_STATUSES]
_ACTIVE_SQL = ",".join("?" * len(_ACTIVE_VALUES))  # "?,?,?" - placeholders only


# ---------- users ----------
def insert_user(conn: sqlite3.Connection, username: str, password_hash: str,
                full_name: str, role: str) -> int:
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
        (username, password_hash, full_name, Role(role).value),
    )
    return cur.lastrowid


def get_user(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _to_user(row) if row else None


def get_user_by_username(conn: sqlite3.Connection, username: str) -> tuple[User, str] | None:
    """Returns (User, password_hash) or None."""
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return (_to_user(row), row["password_hash"]) if row else None


def list_members(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute(
        "SELECT * FROM users WHERE role = ? ORDER BY full_name, id", (Role.MEMBER.value,)
    ).fetchall()
    return [_to_user(r) for r in rows]


# ---------- titles / copies ----------
def insert_title(conn: sqlite3.Connection, title: str, category: str) -> int:
    cur = conn.execute(
        "INSERT INTO titles (title, category) VALUES (?, ?)", (title, category)
    )
    return cur.lastrowid


def insert_copy(conn: sqlite3.Connection, title_id: int, copy_code: str,
                status: CopyStatus = CopyStatus.IN_SERVICE, note: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO copies (title_id, copy_code, status, note) VALUES (?, ?, ?, ?)",
        (title_id, copy_code, CopyStatus(status).value, note),
    )
    return cur.lastrowid


def list_titles(conn: sqlite3.Connection) -> list[Title]:
    rows = conn.execute("SELECT * FROM titles ORDER BY title").fetchall()
    return [_to_title(r) for r in rows]


def get_title(conn: sqlite3.Connection, title_id: int) -> Title | None:
    row = conn.execute("SELECT * FROM titles WHERE id = ?", (title_id,)).fetchone()
    return _to_title(row) if row else None


def list_copies(conn: sqlite3.Connection, title_id: int | None = None) -> list[Copy]:
    """All copies (optionally for one title), ordered by copy_code."""
    if title_id is None:
        rows = conn.execute("SELECT * FROM copies ORDER BY copy_code").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM copies WHERE title_id = ? ORDER BY copy_code", (title_id,)
        ).fetchall()
    return [_to_copy(r) for r in rows]


def get_copy(conn: sqlite3.Connection, copy_id: int) -> Copy | None:
    row = conn.execute("SELECT * FROM copies WHERE id = ?", (copy_id,)).fetchone()
    return _to_copy(row) if row else None


def update_copy_status(conn: sqlite3.Connection, copy_id: int, status: CopyStatus,
                       note: str = "") -> None:
    conn.execute(
        "UPDATE copies SET status = ?, note = ? WHERE id = ?",
        (CopyStatus(status).value, note, copy_id),
    )


# ---------- requests ----------
def insert_request(conn: sqlite3.Connection, member_id: int, title_id: int, copy_id: int,
                   start: date, end: date, status: RequestStatus) -> int:
    """Insert with created_at = now_ts(). The DB trigger may raise
    sqlite3.IntegrityError('COPY_OVERLAP') - let it propagate."""
    cur = conn.execute(
        "INSERT INTO requests (member_id, title_id, copy_id, start_date, end_date, "
        "status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (member_id, title_id, copy_id, start.isoformat(), end.isoformat(),
         RequestStatus(status).value, now_ts()),
    )
    return cur.lastrowid


def get_request(conn: sqlite3.Connection, request_id: int) -> Request | None:
    row = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
    return _to_request(row) if row else None


def list_requests(conn: sqlite3.Connection, member_id: int | None = None,
                  statuses: Iterable[RequestStatus] | None = None,
                  title_id: int | None = None) -> list[Request]:
    """Filtered list, newest first (ORDER BY id DESC)."""
    clauses: list[str] = []
    params: list = []
    if member_id is not None:
        clauses.append("member_id = ?")
        params.append(member_id)
    if title_id is not None:
        clauses.append("title_id = ?")
        params.append(title_id)
    if statuses is not None:
        values = [RequestStatus(s).value for s in statuses]
        if not values:  # explicit empty filter matches nothing
            return []
        clauses.append("status IN (%s)" % ",".join("?" * len(values)))
        params.extend(values)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(
        "SELECT * FROM requests" + where + " ORDER BY id DESC", params
    ).fetchall()
    return [_to_request(r) for r in rows]


def update_request_status(conn: sqlite3.Connection, request_id: int, status: RequestStatus,
                          decision_note: str | None = None,
                          issued_at: str | None = None,
                          returned_at: str | None = None) -> None:
    """Update status; only overwrite the optional columns that are not None."""
    sets = ["status = ?"]
    params: list = [RequestStatus(status).value]
    if decision_note is not None:
        sets.append("decision_note = ?")
        params.append(decision_note)
    if issued_at is not None:
        sets.append("issued_at = ?")
        params.append(issued_at)
    if returned_at is not None:
        sets.append("returned_at = ?")
        params.append(returned_at)
    params.append(request_id)
    conn.execute("UPDATE requests SET " + ", ".join(sets) + " WHERE id = ?", params)


def update_request_copy(conn: sqlite3.Connection, request_id: int, new_copy_id: int) -> None:
    """Used only by the reallocation policy (copy went out of service)."""
    conn.execute("UPDATE requests SET copy_id = ? WHERE id = ?", (new_copy_id, request_id))


def active_commitments_for_copy(conn: sqlite3.Connection, copy_id: int) -> list[Request]:
    """Requests on this copy with status in ACTIVE_STATUSES."""
    rows = conn.execute(
        f"SELECT * FROM requests WHERE copy_id = ? AND status IN ({_ACTIVE_SQL}) "
        "ORDER BY start_date, id",
        [copy_id, *_ACTIVE_VALUES],
    ).fetchall()
    return [_to_request(r) for r in rows]


def active_commitments_for_title(conn: sqlite3.Connection, title_id: int) -> list[Request]:
    """Requests for this title with status in ACTIVE_STATUSES."""
    rows = conn.execute(
        f"SELECT * FROM requests WHERE title_id = ? AND status IN ({_ACTIVE_SQL}) "
        "ORDER BY start_date, id",
        [title_id, *_ACTIVE_VALUES],
    ).fetchall()
    return [_to_request(r) for r in rows]


# ---------- audit ----------
def insert_event(conn: sqlite3.Connection, request_id: int, from_status: str | None,
                 to_status: str, actor: str, note: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO request_events (request_id, from_status, to_status, actor, note, at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (request_id,
         RequestStatus(from_status).value if from_status is not None else None,
         RequestStatus(to_status).value, actor, note, now_ts()),
    )
    return cur.lastrowid


def list_events(conn: sqlite3.Connection, request_id: int) -> list[Event]:
    """Oldest first."""
    rows = conn.execute(
        "SELECT * FROM request_events WHERE request_id = ? ORDER BY id", (request_id,)
    ).fetchall()
    return [_to_event(r) for r in rows]
