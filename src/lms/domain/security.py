"""Password hashing (demo-grade). CONTRACT FILE.

sha256(SALT + password) via stdlib hashlib. Documented limitation: not production
security (single static salt, no key stretching, no lockout).
"""
import hashlib

SALT = "iiit-lms-demo"


def hash_password(password: str) -> str:
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()
