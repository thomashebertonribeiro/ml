"""
FastAPI dependency functions used across routers.

Provides:
- ``get_db``        — async SQLAlchemy session (re-exported from database.py)
- ``get_current_user`` — validates JWT and returns the authenticated User
- ``get_redis``     — async Redis connection
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db  # re-export so callers can import from here
from app.models.user import User
from app.services.auth_service import decode_token
from app.services.exceptions import AuthError
from app.config import settings

# ---------------------------------------------------------------------------
# OAuth2 scheme — extracts the Bearer token from the Authorization header
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ---------------------------------------------------------------------------
# Re-export get_db so routers can import it from a single place
# ---------------------------------------------------------------------------

__all__ = ["get_db", "get_current_user", "get_redis"]


# ---------------------------------------------------------------------------
# Current user dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that validates the JWT Bearer token and returns the
    corresponding ``User`` ORM instance.

    Raises:
        AuthError (HTTP 401): if the token is invalid, expired, or the user
            no longer exists in the database.
    """
    payload = decode_token(token)  # raises AuthError on failure

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AuthError("Token sem identificador de usuário.")

    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise AuthError("Usuário não encontrado.")

    return user


# ---------------------------------------------------------------------------
# Redis dependency
# ---------------------------------------------------------------------------


async def get_redis() -> Redis:  # type: ignore[type-arg]
    """
    Return an async Redis connection.

    The connection is created from ``settings.REDIS_URL`` and closed after
    the request completes.

    Usage::

        @router.get("/example")
        async def example(redis: Redis = Depends(get_redis)):
            ...
    """
    client: Redis = Redis.from_url(  # type: ignore[assignment]
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.aclose()
