from core.models import Post, SearchResponse
from urllib.parse import urljoin
from dotenv import load_dotenv
from scrapling.fetchers import Fetcher
from pathlib import Path
import time
import os

env_path = Path(__file__).resolve().parent
while not (env_path / ".env").exists() and env_path.parent != env_path:
    env_path = env_path.parent
load_dotenv(dotenv_path=env_path / ".env")

class RutrackerScraper:
    source = "rutracker"
    base_url = "https://rutracker.org/forum/"

    def __init__(self):
        raw_cookie = os.getenv("bb_session")
        cleaned_cookie = raw_cookie.strip(' "\'') if raw_cookie else None
        self.cookies = {"bb_session": cleaned_cookie} if cleaned_cookie else {}

    def scrape(self, query: str, max_pages: int = 2, delay: float = 0.1) -> SearchResponse:
        posts: list[Post] = []
        per_page = 50

        for page in range(max_pages):
            search_url = f"{self.base_url.rstrip('/')}/tracker.php?nm={query}&start={page * per_page}"
            try:
                response = Fetcher.get(
                    search_url,
                    cookies=self.cookies,
                    timeout=15,
                    stealthy_headers=True
                )
                print(response.status)

                if response.status != 200:
                    raise RuntimeError(f"Scraper returned status {response.status}")

                links = response.css("a.med.tLink.tt-text.ts-text.hl-tags.bold[href^='viewtopic']")

                if not links:
                    break

                for link in links:
                    title = link.text.strip()
                    url = urljoin(self.base_url, link.attrib["href"])

                    row = link.xpath("ancestor::tr[1]")

                    author_el = row.css("a.med.ts-text[href*='pid=']")
                    author = author_el[0].text.strip() if author_el else "Unknown"

                    seeders_el = row.css("b.seedmed")
                    seeders = seeders_el[0].text.strip() if seeders_el else "Unknown"

                    leechers_el = row.css("td.row4.leechmed.bold")
                    leechers = leechers_el[0].text.strip() if leechers_el else "Unknown"

                    posts.append(Post(
                        id=len(posts) + 1,
                        title=title,
                        url=url,
                        author=author,
                        seeders=seeders,
                        leechers=leechers,
                        source=self.source
                    ))

                time.sleep(delay)

            except Exception as e:
                print(f"Failed to fetch {search_url}: {e}")
                raise

        return SearchResponse(success=True, query=query, data=posts, count=len(posts))