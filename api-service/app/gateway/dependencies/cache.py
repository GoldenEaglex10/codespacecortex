import hashlib
import json
import redis.asyncio as redis
from app.config import settings

# Separate Redis client from rate_limit.py's — same Redis instance, different
# logical use (rate-limit counters vs. cached responses), kept as separate
# client objects so the two concerns don't get tangled together in one file.
cache_client = redis.from_url(settings.redis_url)


def _cache_key(tenant_id: str, question: str) -> str:
    """
    One cache entry per (tenant, question). Hashing the question keeps keys
    a fixed, short length regardless of how long the question text is, and
    avoids putting raw user input directly into a Redis key.
    """
    digest = hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()
    return f"chatcache:{tenant_id}:{digest}"


async def get_cached_response(tenant_id: str, question: str) -> dict | None:
    """Returns the cached response dict, or None on a cache miss."""
    key = _cache_key(tenant_id, question)
    cached = await cache_client.get(key)
    if cached is None:
        return None
    return json.loads(cached)


async def set_cached_response(
    tenant_id: str,
    question: str,
    response: dict,
    ttl: int | None = None,
) -> None:
    """Stores a response, expiring after `ttl` seconds (defaults to CACHE_TTL_SECONDS)."""
    key = _cache_key(tenant_id, question)
    ttl = ttl if ttl is not None else settings.cache_ttl_seconds
    await cache_client.set(key, json.dumps(response), ex=ttl)
