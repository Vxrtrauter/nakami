import json
import time
import redis.asyncio as aioredis

CACHE_TTL = 300
LOCK_TTL = 30  # max seconds a pending lock is held before auto-release

redis: aioredis.Redis = None


async def init_redis(url: str = "redis://localhost:6379"):
    global redis
    redis = aioredis.from_url(url, decode_responses=True)


async def close_redis():
    await redis.aclose()


async def get_cached(q: str) -> dict | None:
    raw = await redis.get(f"cache:{q}")
    if raw is None:
        return None
    result = json.loads(raw)
    result["cached"] = True
    return result


async def set_cached(q: str, response_dict: dict):
    await redis.set(f"cache:{q}", json.dumps(response_dict), ex=CACHE_TTL)


async def acquire_pending_lock(q: str) -> bool:
    key = f"pending:{q}"
    acquired = await redis.set(key, "1", nx=True, ex=LOCK_TTL)
    return acquired is True


async def release_pending_lock(q: str):
    await redis.delete(f"pending:{q}")