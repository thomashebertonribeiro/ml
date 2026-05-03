"""
Rate limiter service — sliding window counter per IP using Redis.

Uses INCR + EXPIRE to implement a simple sliding window:
- On first request in a window, INCR creates the key and EXPIRE sets the TTL.
- Subsequent requests in the same window only INCR (EXPIRE is a no-op when
  the key already has a TTL, so we use EXPIRE only when the key is new).
"""

from __future__ import annotations

from redis.asyncio import Redis


async def check_rate_limit(
    redis: Redis,  # type: ignore[type-arg]
    ip: str,
    limit: int = 60,
    window_seconds: int = 60,
) -> tuple[bool, int]:
    """Verify whether *ip* has exceeded the request rate limit.

    Uses a sliding window implemented with INCR + EXPIRE on a Redis key.
    The key is ``rate_limit:{ip}`` and expires after *window_seconds*.

    Args:
        redis: Async Redis client.
        ip: Client IP address used as the rate-limit identifier.
        limit: Maximum number of requests allowed per window (default: 60).
        window_seconds: Duration of the window in seconds (default: 60).

    Returns:
        A tuple ``(allowed, retry_after)`` where:
        - ``allowed`` is ``True`` if the request is within the limit.
        - ``retry_after`` is the number of seconds until the window resets
          (only meaningful when ``allowed`` is ``False``; 0 otherwise).
    """
    key = f"rate_limit:{ip}"

    # Atomically increment the counter.
    count: int = await redis.incr(key)

    if count == 1:
        # First request in this window — set the expiry.
        await redis.expire(key, window_seconds)

    if count > limit:
        # Retrieve the remaining TTL so we can tell the client when to retry.
        ttl: int = await redis.ttl(key)
        retry_after = max(ttl, 1)  # never return 0 or -1
        return False, retry_after

    return True, 0
