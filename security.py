"""Password hashing utilities."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Optional

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000
SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8


def password_policy_error(password: str) -> Optional[str]:
    """Return a validation error for new/reset credentials, else None.

    Existing stored hashes remain verifiable; this policy applies only when
    creating or resetting passwords.
    """
    value = str(password or "")
    if len(value) < MIN_PASSWORD_LENGTH:
        return f"Password must contain at least {MIN_PASSWORD_LENGTH} characters."
    if not any(ch.isalpha() for ch in value):
        return "Password must contain at least one letter."
    if not any(ch.isdigit() for ch in value):
        return "Password must contain at least one digit."
    return None


def password_is_strong(password: str) -> bool:
    return password_policy_error(password) is None


def hash_password(password: str) -> str:
    policy_error = password_policy_error(password)
    if policy_error:
        raise ValueError(policy_error)
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored_hash: Optional[str]) -> bool:
    if not password or not stored_hash:
        return False
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False
