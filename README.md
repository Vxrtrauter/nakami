# Nakami

A FastAPI-powered server for searching torrent trackers and various web pages. This project provides a unified search API that aggregates results from (soon) multiple scrapers with Redis-based caching for improved performance.

This project is part of [SoftwareManager](https://github.com/KeksPirates/SoftwareManager).

## Features

- **FastAPI Backend**: High-performance async web framework
- **Multi-Scraper Support**: Extensible scraper system for different sources
- **Redis Caching**: Efficient caching with pub/sub for concurrent requests
- **Torrent Search**: Currently supports Rutracker.org

## Installation

### Prerequisites

- Python 3.8+
- Redis server running at `redis://localhost:6379`

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Vxrtrauter/nakami
cd nakami
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with:
```env
bb_session=your_rutracker_session_cookie
```

4. Run the server:
```bash
uvicorn src.main:app --reload
```

The server will start at `http://localhost:8000`

## Usage

### API Endpoints

#### GET /search
Search across all configured scrapers.

**Parameters:**
- `q` (string): Search query (required)

**Example:**
```bash
curl "http://localhost:8000/search?q=keks"
```

**Response:**
```json
{
    "cached": false,
    "count": 1,
    "data": [
        {
        "author": "Viterrson",
        "id": 1,
        "leechers": 0,
        "seeders": 3,
        "title": "(Hard - Rock) Keks - Keks - 1983, MP3, 320 kbps",
        "url": "https://rutracker.org/forum/viewtopic.php?t=3835559",
        "source": "rutracker"
        }
    ],
    "query": "keks",
    "success": true
}

```

#### GET /ping
Health check endpoint.

**Example:**
```bash
curl http://localhost:8000/ping
```

**Response:**
```json
{
  "message": "pong"
}
```

## Configuration

### Environment Variables

- `bb_session`: Rutracker session cookie for requests

### Redis Configuration

The application expects a Redis server running at `redis://localhost:6379` by default. To use a different Redis instance, modify the connection URL in the code.

### Adding New Scrapers

1. Create a new scraper class in `src/scrapers/`
2. Implement the scraper interface (see `RutrackerScraper` for example)
3. Register it in `src/scrapers/__init__.py`

Example scraper structure:
```python
class MyScraper:
    source = "my_source"
    base_url = "https://example.com"

    def scrape(self, query: str) -> SearchResponse:
        # Implementation here
        pass
```

## Project Structure

```
nakami/
├── src/
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── cache.py         # Redis caching utilities
│   │   └── models.py        # Data models
│   └── scrapers/
│       ├── __init__.py      # Scraper registry
│       └── rutracker.py     # Rutracker scraper
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── LICENSE                  # GNU AGPL v3
```

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This project is for educational purposes only. Please respect the terms of service of the websites you scrape and ensure compliance with applicable laws and regulations.
