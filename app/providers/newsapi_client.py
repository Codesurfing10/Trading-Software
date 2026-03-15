"""NewsAPI client – top headlines and keyword/symbol search."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app import cache
from app.config import settings

log = logging.getLogger(__name__)

_BASE = "https://newsapi.org/v2"
_NEWS_TTL = 300  # 5 minutes


def _headers() -> Dict[str, str]:
    return {"X-Api-Key": settings.newsapi_api_key}


async def get_top_headlines(
    category: str = "business",
    country: str = "us",
    page_size: int = 20,
) -> Dict[str, Any]:
    """Fetch top headlines from NewsAPI."""
    if not settings.newsapi_api_key:
        return {"error": "NEWSAPI_API_KEY not configured", "articles": []}

    cache_key = f"headlines:{country}:{category}:{page_size}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_BASE}/top-headlines",
                params={
                    "category": category,
                    "country": country,
                    "pageSize": page_size,
                },
                headers=_headers(),
            )
            r.raise_for_status()
            data = r.json()
            cache.set(cache_key, data, ttl=_NEWS_TTL)
            return data
    except httpx.HTTPStatusError as exc:
        log.warning("NewsAPI HTTP error: %s", exc)
        if exc.response.status_code == 401:
            return {"error": "Invalid or missing NEWSAPI_API_KEY", "articles": []}
        return {"error": str(exc), "articles": []}
    except Exception as exc:  # noqa: BLE001
        log.warning("NewsAPI error: %s", exc)
        return {"error": str(exc), "articles": []}


async def search_news(
    query: str,
    sort_by: str = "publishedAt",
    page_size: int = 20,
    language: str = "en",
) -> Dict[str, Any]:
    """Search news articles by keyword/company/ticker."""
    if not settings.newsapi_api_key:
        return {"error": "NEWSAPI_API_KEY not configured", "articles": []}

    cache_key = f"search:{query}:{sort_by}:{page_size}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_BASE}/everything",
                params={
                    "q": query,
                    "sortBy": sort_by,
                    "pageSize": page_size,
                    "language": language,
                },
                headers=_headers(),
            )
            r.raise_for_status()
            data = r.json()
            cache.set(cache_key, data, ttl=_NEWS_TTL)
            return data
    except httpx.HTTPStatusError as exc:
        log.warning("NewsAPI search HTTP error: %s", exc)
        if exc.response.status_code == 401:
            return {"error": "Invalid or missing NEWSAPI_API_KEY", "articles": []}
        return {"error": str(exc), "articles": []}
    except Exception as exc:  # noqa: BLE001
        log.warning("NewsAPI search error: %s", exc)
        return {"error": str(exc), "articles": []}


async def get_symbol_news(symbol: str, page_size: int = 15) -> Dict[str, Any]:
    """Return news articles for a stock symbol."""
    return await search_news(query=symbol, page_size=page_size)
