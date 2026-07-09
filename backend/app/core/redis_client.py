"""
Redis connection and JWT blocklist helpers.

Provides:
    get_redis            — cached redis.Redis client, built from settings.REDIS_URL
    blocklist_token       — add a JWT to the blocklist on logout (T-016)
    is_token_blocklisted  — check whether a token has been logged out; will be
                            used by get_current_user (T-018) to reject
                            blocklisted tokens on subsequent requests
"""
from functools import lru_cache

import redis

from app.core.config import settings

BLOCKLIST_PREFIX = "blocklist:"

# Without explicit timeouts, redis-py will hang indefinitely on a bad
# connection (wrong host, firewalled port, TLS mismatch, etc.) instead of
# raising — which turns a Redis outage into a request that never
# completes. 5s is generous for Upstash's normal latency but still fails
# fast enough to be debuggable.
_CONNECT_TIMEOUT_SECONDS = 5
_SOCKET_TIMEOUT_SECONDS = 5


@lru_cache
def get_redis() -> redis.Redis:
    """Return a cached Redis client built from settings.REDIS_URL (Upstash)."""
    return redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=_SOCKET_TIMEOUT_SECONDS,
    )


def blocklist_token(token: str, ttl_seconds: int) -> None:
    """
    Add a JWT to the Redis blocklist for `ttl_seconds` (US-003, T-016).

    ttl_seconds should be the token's remaining lifetime (exp - now) so the
    blocklist entry self-expires at the same moment the token would have
    stopped being valid anyway. This means the blocklist never grows
    unbounded and needs no manual cleanup job.
    """
    if ttl_seconds <= 0:
        # Token is already expired — nothing to blocklist, it's dead already.
        return
    client = get_redis()
    client.setex(f"{BLOCKLIST_PREFIX}{token}", ttl_seconds, "1")


def is_token_blocklisted(token: str) -> bool:
    """Check whether a token has been logged out. Used by get_current_user (T-018)."""
    client = get_redis()
    return bool(client.exists(f"{BLOCKLIST_PREFIX}{token}"))

