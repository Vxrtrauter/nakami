from core.models import Post, SearchResponse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from scrapling.fetchers import Fetcher
import time
import os

load_dotenv()

cookies = {
    "bb_session": os.getenv("bb_session")
}


def scrape_rutracker(query: str, max_pages: int = 2, delay: float = 0.1) -> SearchResponse:
    posts: list[Post] = []
    per_page = 50
    base_url = "https://rutracker.org/forum/"

    for page in range(max_pages):
        search_url = f"{base_url.rstrip('/')}/tracker.php?nm={query}&start={page * per_page}"
        print(search_url)
        try:
            response = Fetcher.get(
                search_url,
                cookies=cookies,
                timeout=15,
                stealthy_headers=True
            )
            print(response.status)

            if response.status != 200:
                break

            soup = BeautifulSoup(response.body, 'html.parser')  # body is bytes, pass directly
            links = soup.find_all('a', class_="med tLink tt-text ts-text hl-tags bold", href=lambda x: x and x.startswith("viewtopic"))

            if not links:
                break

            for link in links:
                title = link.text.strip()
                url = urljoin(base_url, link['href'])

                author_link = link.find_parent('tr').find('a', class_="med ts-text")
                author = author_link.text.strip() if author_link else "Unknown"

                seeders_link = link.find_parent('tr').find('b', class_="seedmed")
                seeders = seeders_link.text.strip() if seeders_link else "Unknown"

                leechers_link = link.find_parent('tr').find('td', class_="row4 leechmed bold")
                leechers = leechers_link.text.strip() if leechers_link else "Unknown"

                posts.append(Post(
                    id=len(posts) + 1,
                    title=title,
                    url=url,
                    author=author,
                    seeders=seeders,
                    leechers=leechers
                ))

            time.sleep(delay)
        except Exception as e:
            print(f"Failed to fetch {search_url}: {e}")
            break

    return SearchResponse(success=True, query=query, data=posts, count=len(posts))