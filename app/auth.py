import hashlib
import hmac
import os

from fastapi import HTTPException, Request

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pharmagraph.local").strip().lower()
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")


def verify_password(password: str) -> bool:
    try:
        salt_hex, expected_hex = ADMIN_PASSWORD_HASH.split(":", 1)

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            600_000,
        )

        return hmac.compare_digest(actual, expected)

    except (ValueError, TypeError):
        return False


def require_admin(request: Request) -> str:
    user = request.session.get("user")

    if user != ADMIN_EMAIL:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return user
