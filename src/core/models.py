from dataclasses import dataclass

@dataclass
class Post:
    id: int
    title: str
    url: str
    author: str = ""
    seeders: str = ""
    leechers: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()

@dataclass
class SearchResponse:
    success: bool
    query: str
    data: list[Post]
    count: int
    cached: bool = False

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "query": self.query,
            "data": [p.to_dict() for p in self.data],
            "count": self.count,
            "cached": self.cached,
        }