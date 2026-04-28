from core.models import Post, SearchResponse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import cloudscraper
import requests
import time
import os

load_dotenv()

scraper = cloudscraper.create_scraper()

cookies = {
    "bb_session": os.getenv("bb_session")
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0"
}


def scrape_rutracker(query: str, max_pages: int = 2, delay: float = 0.1) -> SearchResponse:
    posts: list[Post] = []
    per_page = 50
    base_url = "https://rutracker.org/forum/"
    for page in range(max_pages):
        search_url = f"{base_url.rstrip('/')}/tracker.php?nm={query}&start={page * per_page}"
        print(search_url)
        try:
            response = scraper.get(search_url, cookies=cookies, headers=headers, timeout=15)
            print(response.status_code)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
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
        except requests.RequestException as e:
            print(f"Failed to fetch {search_url}: {e}")
            break
    return SearchResponse(success=True, query=query, data=posts, count=len(posts))