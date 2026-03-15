"""Markets routes – stock quotes for the configured watchlist."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.config import settings
from app.providers import finnhub_client

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("/quotes")
async def get_quotes(
    symbols: Optional[str] = Query(
        default=None,
        description="Comma-separated list of symbols. Defaults to watchlist.",
    )
):
    """Return quotes for the watchlist (or a custom list of symbols)."""
    symbol_list: List[str] = (
        [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if symbols
        else settings.watchlist_symbols
    )
    quotes = await finnhub_client.get_quotes(symbol_list)
    return {"symbols": symbol_list, "quotes": quotes}


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Return a single quote for *symbol*."""
    data = await finnhub_client.get_quote(symbol.upper())
    return data


@router.get("/search")
async def search_symbols(q: str = Query(..., min_length=1)):
    """Search for symbols matching *q*."""
    results = await finnhub_client.search_symbols(q)
    return {"results": results}
