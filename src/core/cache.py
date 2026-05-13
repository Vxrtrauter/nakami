import json
import redis.asyncio as aioredis

CACHE_TTL = 300
LOCK_TTL = 30

_redis: aioredis.Redis = None


def get_redis() -> aioredis.Redis:
    return _redis


async def init_redis(url: str = "redis://localhost:6379"):
    global _redis
    _redis = aioredis.from_url(url, decode_responses=True)


async def close_redis():
    await _redis.aclose()


async def get_cached(q: str) -> dict | None:
    raw = await _redis.get(f"cache:{q}")
    if raw is None:
        return None
    result = json.loads(raw)
    result["cached"] = True
    return result


async def set_cached(q: str, response_dict: dict):
    await _redis.set(f"cache:{q}", json.dumps(response_dict), ex=CACHE_TTL)


async def acquire_pending_lock(q: str) -> bool:
    acquired = await _redis.set(f"pending:{q}", "1", nx=True, ex=LOCK_TTL)
    return acquired is True


async def release_pending_lock(q: str):
    await _redis.delete(f"pending:{q}")