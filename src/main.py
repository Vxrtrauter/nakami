import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from core.models import SearchResponse
from core.cache import evict_expired, get_cached, set_cached, get_or_create_pending_lock
from scrapers import SCRAPERS


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(evict_expired())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/search")
async def search(q: str = Query(default="")):
    if not q:
        raise HTTPException(status_code=400, detail=SearchResponse(
            success=False, query="", data=[], count=0
        ).to_dict())

    cached = await get_cached(q)
    if cached:
        return cached

    term_lock = await get_or_create_pending_lock(q)

    async with term_lock:
        cached = await get_cached(q)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        results = await asyncio.gather(*[
            loop.run_in_executor(None, scraper.scrape, q)
            for scraper in SCRAPERS
        ], return_exceptions=True)

        all_posts = []
        for r in results:
            if isinstance(r, Exception):
                continue
            all_posts.extend(r.data)

        response = SearchResponse(success=True, query=q, data=all_posts, count=len(all_posts))
        response_dict = response.to_dict()
        await set_cached(q, response_dict)
        return response_dict


@app.get("/ping")
async def ping():
    return {"message": "pong"}