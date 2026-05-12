from core.models import Post, SearchResponse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from scrapling.fetchers import Fetcher
import time
import os

load_dotenv()

class RutrackerScraper():
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

                soup = BeautifulSoup(response.body, "html.parser")
                links = soup.find_all("a", class_="med tLink tt-text ts-text hl-tags bold", href=lambda x: x and x.startswith("viewtopic"))

                if not links:
                    break

                for link in links:
                    row = link.find_parent("tr")
                    title = link.text.strip()
                    url = urljoin(self.base_url, link["href"])
                    author_el = row.find("a", class_="med ts-text")
                    seeders_el = row.find("b", class_="seedmed")
                    leechers_el = row.find("td", class_="row4 leechmed bold")

                    posts.append(Post(
                        id=len(posts) + 1,
                        title=title,
                        url=url,
                        author=author_el.text.strip() if author_el else "Unknown",
                        seeders=seeders_el.text.strip() if seeders_el else "Unknown",
                        leechers=leechers_el.text.strip() if leechers_el else "Unknown",
                        source=self.source,
                    ))

                time.sleep(delay)

            except Exception as e:
                print(f"Failed to fetch {search_url}: {e}")
                break

        return SearchResponse(success=True, query=query, data=posts, count=len(posts))