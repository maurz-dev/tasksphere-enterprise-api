"""Cryptographic security utilities for password hashing and JWT issuance.

Uses bcrypt directly for robust, future-proof password hashing (PEP 506 / FIPS)
and PyJWT for stateless JSON Web Token generation.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, Union

import bcrypt
import jwt

from enterprise_api.core.config import settings


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt with automatic salting."""
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt-hashed string."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta | None = None,
    claims: dict[str, Any] | None = None,
) -> str:
    """Issue a signed JWT access token containing subject and optional claims."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "nbf": now,
        "exp": expire,
        "iss": settings.APP_NAME,
    }

    if claims:
        payload.update(claims)

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Raises:
        jwt.PyJWTError: If token is expired, corrupted, or signature fails.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        issuer=settings.APP_NAME,
        options={"require": ["exp", "sub", "iat"]},
    )
