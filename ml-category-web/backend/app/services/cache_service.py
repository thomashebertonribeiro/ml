"""
Cache service — thin wrapper around Redis for JSON response caching.

All Redis exceptions are caught silently: a warning is logged and the
caller receives ``None`` (cache miss), allowing the application to fall
back to the database without crashing.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def get_cached(redis: Redis, key: str) -> dict | None:  # type: ignore[type-arg]
    """Retrieve a cached JSON value from Redis.

    Args:
        redis: Async Redis client.
        key: Cache key.

    Returns:
        The deserialized dict if the key exists and is valid JSON,
        otherwise ``None``.
    """
    try:
        raw = await redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache GET failed for key=%r: %s", key, exc)
        return None


async def set_cached(
    redis: Redis,  # type: ignore[type-arg]
    key: str,
    value: Any,
    ttl_seconds: int = 300,
) -> None:
    """Serialize *value* to JSON and store it in Redis with an expiry.

    Args:
        redis: Async Redis client.
        key: Cache key.
        value: Any JSON-serializable value.
        ttl_seconds: Time-to-live in seconds (default 5 minutes).
    """
    try:
        serialized = json.dumps(value)
        await redis.set(key, serialized, ex=ttl_seconds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache SET failed for key=%r: %s", key, exc)


async def invalidate(redis: Redis, pattern: str) -> None:  # type: ignore[type-arg]
    """Delete all keys matching *pattern* using SCAN + DEL.

    Uses the non-blocking SCAN command to iterate over matching keys in
    batches, then deletes them.  Redis exceptions are caught silently.

    Args:
        redis: Async Redis client.
        pattern: Glob-style pattern (e.g. ``"categories:*"``).
    """
    try:
        cursor: int = 0
        while True:
            cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache INVALIDATE failed for pattern=%r: %s", pattern, exc)
