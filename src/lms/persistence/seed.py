"""Initial library data from the problem statement.  OWNER: Person 3 (see docs/team/3.md).

Preserve the PDF's meaning exactly (business date defaults to 2026-08-01):

| Title (category)                                   | Copies | Current information                                   |
|----------------------------------------------------|--------|-------------------------------------------------------|
| Clean Code (Software Engineering)                  | 4      | CC-1, CC-2 ISSUED 2026-07-21 -> 2026-08-04            |
| Introduction to Algorithms (Algorithms)            | 3      | ITA-1 RESERVED 2026-08-04 -> 2026-08-08               |
| Design Patterns (Software Design)                  | 2      | DP-2 status DAMAGED                                   |
| Database System Concepts (Databases)               | 5      | all available                                         |
| Artificial Intelligence: A Modern Approach (AI)    | 3      | AIMA-1 ISSUED 2026-07-21 -> 2026-08-04;               |
|                                                    |        | AIMA-2 RESERVED 2026-08-06 -> 2026-08-07 (different copy) |

Assumptions (documented in docs/04-assumptions-and-scope.md, A10): issue start dates are not in the
PDF -> reconstructed as 14 days before the due date; "1 issued + 1 reserved" means
two different copies.

Copy codes: CC-1..CC-4, ITA-1..ITA-3, DP-1..DP-2, DSC-1..DSC-5, AIMA-1..AIMA-3.

Users (password via lms.domain.security.hash_password):
  librarian / lib123  LIBRARIAN  "Library Staff"
  asha  / pass123     MEMBER     "Asha Rao"
  ravi  / pass123     MEMBER     "Ravi Kumar"
  meera / pass123     MEMBER     "Meera Iyer"
  kiran / pass123     MEMBER     "Kiran Das"
Seeded commitments belong to: CC-1 asha, CC-2 ravi, ITA-1 meera, AIMA-1 kiran, AIMA-2 asha.
Insert them via repo.insert_request + repo.insert_event(actor="seed").
"""
from __future__ import annotations

import sqlite3
from datetime import date

from lms.domain.models import CopyStatus, RequestStatus, Role
from lms.persistence import db
from lms.persistence import repository as repo
from lms.domain.security import hash_password


def seed(conn: sqlite3.Connection) -> None:
    """Insert the data above into an EMPTY schema."""
    users = [
        ("librarian", "lib123", "Library Staff", Role.LIBRARIAN),
        ("asha", "pass123", "Asha Rao", Role.MEMBER),
        ("ravi", "pass123", "Ravi Kumar", Role.MEMBER),
        ("meera", "pass123", "Meera Iyer", Role.MEMBER),
        ("kiran", "pass123", "Kiran Das", Role.MEMBER),
    ]
    user_ids = {
        username: repo.insert_user(conn, username, hash_password(password), full_name, role.value)
        for username, password, full_name, role in users
    }

    title_data = [
        ("Clean Code", "Software Engineering", ["CC-1", "CC-2", "CC-3", "CC-4"]),
        ("Introduction to Algorithms", "Algorithms", ["ITA-1", "ITA-2", "ITA-3"]),
        ("Design Patterns", "Software Design", ["DP-1", "DP-2"]),
        ("Database System Concepts", "Databases", ["DSC-1", "DSC-2", "DSC-3", "DSC-4", "DSC-5"]),
        (
            "Artificial Intelligence: A Modern Approach",
            "AI",
            ["AIMA-1", "AIMA-2", "AIMA-3"],
        ),
    ]
    title_ids = {}
    for title, category, copy_codes in title_data:
        title_id = repo.insert_title(conn, title, category)
        title_ids[title] = title_id
        for copy_code in copy_codes:
            status = CopyStatus.DAMAGED if copy_code == "DP-2" else CopyStatus.IN_SERVICE
            repo.insert_copy(conn, title_id, copy_code, status)

    commitments = [
        ("asha", "Clean Code", "CC-1", date(2026, 7, 21), date(2026, 8, 4), RequestStatus.ISSUED),
        ("ravi", "Clean Code", "CC-2", date(2026, 7, 21), date(2026, 8, 4), RequestStatus.ISSUED),
        (
            "meera", "Introduction to Algorithms", "ITA-1",
            date(2026, 8, 4), date(2026, 8, 8), RequestStatus.RESERVED,
        ),
        (
            "kiran", "Artificial Intelligence: A Modern Approach", "AIMA-1",
            date(2026, 7, 21), date(2026, 8, 4), RequestStatus.ISSUED,
        ),
        (
            "asha", "Artificial Intelligence: A Modern Approach", "AIMA-2",
            date(2026, 8, 6), date(2026, 8, 7), RequestStatus.RESERVED,
        ),
    ]
    copies = {copy.copy_code: copy for copy in repo.list_copies(conn)}
    for member, title, copy_code, start, end, status in commitments:
        request_id = repo.insert_request(
            conn, user_ids[member], title_ids[title], copies[copy_code].id,
            start, end, status,
        )
        repo.insert_event(conn, request_id, None, status.value, "seed")


def reset_db() -> None:
    """Drop everything, init schema, seed. Used by the 'Reset demo data' button and tests."""
    conn = db.get_conn()
    try:
        db.drop_all(conn)
        db.init_db(conn)
    finally:
        conn.close()
    with db.transaction() as conn:
        seed(conn)


def ensure_db() -> None:
    """Init + seed only if the DB has no titles yet (called on app start)."""
    conn = db.get_conn()
    try:
        db.init_db(conn)
        has_titles = conn.execute("SELECT COUNT(*) FROM titles").fetchone()[0] > 0
    finally:
        conn.close()
    if not has_titles:
        with db.transaction() as conn:
            seed(conn)


# Run from the project root:  python -m lms.persistence.seed
if __name__ == "__main__":
    reset_db()
    print("Database reset and seeded.")
