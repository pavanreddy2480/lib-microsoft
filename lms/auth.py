"""Simple login (demo-grade).  OWNER: Person 2 (see tasks/2.md).

Passwords: sha256(SALT + password) hex digest via stdlib hashlib.
Documented limitation: not production security (no per-user salt, no lockout).
"""
from __future__ import annotations

from .models import Role, User

SALT = "iiit-lms-demo"


def hash_password(password: str) -> str:
    raise NotImplementedError


def login(username: str, password: str) -> User:
    """Open a connection, look the user up, compare hashes.

    Raises BusinessRuleError(LOGIN_FAILED, "Invalid username or password.")
    on unknown user OR wrong password (same message for both).
    """
    raise NotImplementedError


def require_role(user: User | None, role: Role) -> None:
    """Raise BusinessRuleError(NOT_AUTHORIZED, ...) if user is None or has another role."""
    raise NotImplementedError
