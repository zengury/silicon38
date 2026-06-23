"""
Password hashing utilities.

Uses SHA-256 for backward compatibility with existing user records.
All existing user passwords in production are stored with SHA-256 hashes
(or MD5 for legacy accounts).  bcrypt migration is planned for Phase 2
but requires a coordinated hash-upgrade strategy.

Usage::

    from core.security import hash_password, verify_password

    hashed = hash_password("my-password")
    assert verify_password("my-password", hashed) is True
"""

import hashlib


def hash_password(password: str) -> str:
    """Return a SHA-256 hex digest of `password`.

    This matches the hash format used in the existing user table.
    Passwords are NOT salted (legacy constraint) — only use this for
    backward-compatible comparison.  New password-storage schemes should
    use bcrypt via a separate utility.
    """
    if not password:
        raise ValueError("password must not be empty")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Compare `plain` against a previously-hashed password using SHA-256.

    Returns True if the hash matches, False otherwise.
    """
    if not plain or not hashed:
        return False
    candidate = hash_password(plain)
    # Constant-time comparison to avoid timing attacks
    return _constant_time_compare(candidate.encode(), hashed.encode())


def _constant_time_compare(a: bytes, b: bytes) -> bool:
    """Return a == b using a constant-time comparison to mitigate timing attacks."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    return result == 0
