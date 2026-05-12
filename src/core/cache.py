import asyncio
import time

CACHE_TTL = 300

cache: dict[str, tuple[dict, float]] = {}
cache_lock = asyncio.Lock()
pending_locks: dict[str, asyncio.Lock] = {}


async def evict_expired():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        async with cache_lock:
            expired = [k for k, (_, ts) in cache.items() if now - ts >= CACHE_TTL]
            for k in expired:
                del cache[k]
                pending_locks.pop(k, None)


async def get_cached(q: str) -> dict | None:
    async with cache_lock:
        if q in cache:
            result = cache[q][0].copy()
            result["cached"] = True
            return result
    return None


async def set_cached(q: str, response_dict: dict):
    async with cache_lock:
        cache[q] = (response_dict, time.time())


async def get_or_create_pending_lock(q: str) -> asyncio.Lock:
    async with cache_lock:
        if q not in pending_locks:
            pending_locks[q] = asyncio.Lock()
        return pending_locks[q]