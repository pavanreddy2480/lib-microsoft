"""Simple login (demo-grade).  OWNER: Person 2 (see docs/team/2.md).

Password hashing lives in lms.domain.security (shared with seed data).
"""
from __future__ import annotations

from contextlib import closing

from lms.domain.errors import LOGIN_FAILED, NOT_AUTHORIZED, BusinessRuleError
from lms.domain.models import Role, User
from lms.domain.security import hash_password
from lms.persistence import db
from lms.persistence import repository as repo

def login(username: str, password: str) -> User:
    """Open a connection, look the user up, compare hash_password(password) with the stored hash.

    Raises BusinessRuleError(LOGIN_FAILED, "Invalid username or password.")
    on unknown user OR wrong password (same message for both).
    """
    with closing(db.get_conn()) as conn:
        found = repo.get_user_by_username(conn, (username or "").strip())
    if found is None:
        raise BusinessRuleError(LOGIN_FAILED, "Invalid username or password.")
    user, stored_hash = found
    if hash_password(password or "") != stored_hash:
        raise BusinessRuleError(LOGIN_FAILED, "Invalid username or password.")
    return user


def require_role(user: User | None, role: Role) -> None:
    """Raise BusinessRuleError(NOT_AUTHORIZED, ...) if user is None or has another role."""
    if user is None or user.role != role:
        raise BusinessRuleError(
            NOT_AUTHORIZED, f"This action requires the {role.value} role."
        )
