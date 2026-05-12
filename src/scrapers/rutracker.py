from core.models import Post, SearchResponse
from urllib.parse import urljoin
from dotenv import load_dotenv
from scrapling.fetchers import Fetcher
import time
import os

load_dotenv()

class RutrackerScraper:
    source = "rutracker"
    base_url = "https://rutracker.org/forum/"

    def __init__(self):
        self.cookies = {"bb_session": os.getenv("bb_session")}

    def scrape(self, query: str, max_pages: int = 2, delay: float = 0.1) -> SearchResponse:
        posts: list[Post] = []
        per_page = 50

        for page in range(max_pages):
            search_url = f"{self.base_url.rstrip('/')}/tracker.php?nm={query}&start={page * per_page}"
            print(search_url)
            try:
                response = Fetcher.get(
                    search_url,
                    cookies=self.cookies,
                    timeout=15,
                    stealthy_headers=True
                )
                print(response.status)
                if response.status != 200:
                    break

                links = response.css('a.med.tLink.tt-text.ts-text.hl-tags.bold[href^="viewtopic"]')
                if not links:
                    break

                for link in links:
                    row = link.parent.parent  # td --> tr
                    posts.append(Post(
                        id=len(posts) + 1,
                        title=link.text.strip(),
                        url=urljoin(self.base_url, link.attrib["href"]),
                        author=row.css_first("a.med.ts-text").text.strip() if row.css_first("a.med.ts-text") else "Unknown",
                        seeders=row.css_first("b.seedmed").text.strip() if row.css_first("b.seedmed") else "Unknown",
                        leechers=row.css_first("td.row4.leechmed.bold").text.strip() if row.css_first("td.row4.leechmed.bold") else "Unknown",
                        source=self.source,
                    ))

                time.sleep(delay)

            except Exception as e:
                print(f"Failed to fetch {search_url}: {e}")
                break

        return SearchResponse(success=True, query=query, data=posts, count=len(posts))