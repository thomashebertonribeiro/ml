"""
Authentication service: password hashing and JWT token management.

Uses passlib[bcrypt] for password hashing and python-jose for JWT.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.services.exceptions import AuthError

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the bcrypt *hashed* value."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def create_access_token(user_id: str, email: str) -> str:
    """
    Create a signed JWT access token for the given user.

    The token expires in ``settings.ACCESS_TOKEN_EXPIRE_SECONDS`` seconds
    (default 24 h).  The payload includes:

    * ``sub`` — user UUID as string
    * ``email`` — user e-mail address
    * ``exp`` — expiry timestamp (UTC)
    * ``iat`` — issued-at timestamp (UTC)
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)

    payload: dict = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Validate and decode a JWT access token.

    Returns the decoded payload dict on success.

    Raises:
        AuthError: if the token is invalid, expired, or missing required claims.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AuthError("Token inválido ou expirado.") from exc

    # Ensure required claims are present
    if payload.get("sub") is None or payload.get("email") is None:
        raise AuthError("Token com payload inválido.")

    return payload
