import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from core.models import SearchResponse
from core.cache import (
    init_redis, close_redis,
    get_redis,
    get_cached, set_cached,
    acquire_pending_lock, release_pending_lock
)
from scrapers import SCRAPERS

PUBSUB_CHANNEL = "cache_ready:"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis(os.getenv("REDIS_URL", "redis://localhost:6379"))
    yield
    await close_redis()


app = FastAPI(lifespan=lifespan)


async def wait_for_result(q: str, timeout: float = 10.0) -> dict | None:
    pubsub = get_redis().pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL + q)
    try:
        deadline = asyncio.get_event_loop().time() + timeout
        async for message in pubsub.listen():
            if message["type"] == "message":
                return await get_cached(q)
            if asyncio.get_event_loop().time() > deadline:
                return None
    finally:
        await pubsub.unsubscribe(PUBSUB_CHANNEL + q)
        await pubsub.aclose()


@app.get("/search")
async def search(q: str = Query(default="")):
    if not q:
        raise HTTPException(status_code=400, detail=SearchResponse(
            success=False, query="", data=[], count=0
        ).to_dict())

    cached = await get_cached(q)
    if cached:
        return cached

    got_lock = await acquire_pending_lock(q)

    if not got_lock:
        result = await wait_for_result(q)
        if result:
            return result
        return SearchResponse(success=False, query=q, data=[], count=0).to_dict()

    try:
        cached = await get_cached(q)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        results = await asyncio.gather(*[
            loop.run_in_executor(None, scraper.scrape, q)
            for scraper in SCRAPERS
        ], return_exceptions=True)

        all_posts = []
        has_errors = False
        for r in results:
            if isinstance(r, Exception):
                has_errors = True
                continue
            all_posts.extend(r.data)

        response = SearchResponse(success=True, query=q, data=all_posts, count=len(all_posts))
        response_dict = response.to_dict()

        if all_posts or not has_errors:
            await set_cached(q, response_dict)
            
        await get_redis().publish(PUBSUB_CHANNEL + q, "ready")

        return response_dict

    finally:
        await release_pending_lock(q)


@app.get("/ping")
async def ping():
    return {"message": "pong"}