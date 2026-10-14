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

Assumptions (documented in docs/ASSUMPTIONS.md): issue start dates are not in the
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
    raise NotImplementedError


def reset_db() -> None:
    """Drop everything, init schema, seed. Used by the 'Reset demo data' button and tests."""
    raise NotImplementedError


def ensure_db() -> None:
    """Init + seed only if the DB has no titles yet (called on app start)."""
    raise NotImplementedError


# Run from the project root:  python -m lms.persistence.seed
if __name__ == "__main__":
    reset_db()
    print("Database reset and seeded.")
