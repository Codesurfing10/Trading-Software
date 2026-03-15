"""News routes – headlines and keyword/symbol search via NewsAPI."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.providers import newsapi_client

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/headlines")
async def get_headlines(
    category: str = Query(default="business"),
    country: str = Query(default="us"),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Return top business/financial headlines."""
    return await newsapi_client.get_top_headlines(
        category=category,
        country=country,
        page_size=page_size,
    )


@router.get("/search")
async def search_news(
    q: str = Query(..., min_length=1, description="Search keyword or ticker symbol"),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="publishedAt"),
):
    """Search news articles by keyword or ticker symbol."""
    return await newsapi_client.search_news(
        query=q,
        sort_by=sort_by,
        page_size=page_size,
    )


@router.get("/symbol/{symbol}")
async def get_symbol_news(symbol: str, page_size: int = Query(default=15)):
    """Return news articles for a specific ticker symbol."""
    return await newsapi_client.get_symbol_news(
        symbol=symbol.upper(),
        page_size=page_size,
    )
