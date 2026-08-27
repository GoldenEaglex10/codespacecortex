from fastapi import Depends, HTTPException
import redis.asyncio as redis
from app.config import settings
from app.gateway.dependencies.auth import verify_jwt

redis_client = redis.from_url(settings.redis_url)

async def rate_limit(claims: dict = Depends(verify_jwt)):
    key = f"ratelimit:{claims['tenant_id']}:{claims['student_id']}"
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, 60, nx=True)
        count, _ = await pipe.execute()
    if count > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": "60"})
