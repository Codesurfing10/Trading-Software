"""Finnhub REST client – stock quotes and option chains (best-effort)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app import cache
from app.config import settings

log = logging.getLogger(__name__)

_BASE = "https://finnhub.io/api/v1"
_QUOTE_TTL = 30   # seconds
_OPTION_TTL = 120


def _headers() -> Dict[str, str]:
    return {"X-Finnhub-Token": settings.finnhub_api_key}


async def get_quote(symbol: str) -> Dict[str, Any]:
    """Return real-time quote for *symbol*.  Returns {} on error."""
    if not settings.finnhub_api_key:
        return {"error": "FINNHUB_API_KEY not configured", "symbol": symbol}

    cache_key = f"quote:{symbol}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_BASE}/quote",
                params={"symbol": symbol},
                headers=_headers(),
            )
            r.raise_for_status()
            data = r.json()
            # Enrich with the symbol so callers don't have to pass it separately
            data["symbol"] = symbol
            cache.set(cache_key, data, ttl=_QUOTE_TTL)
            return data
    except httpx.HTTPStatusError as exc:
        log.warning("Finnhub quote HTTP error for %s: %s", symbol, exc)
        return {"error": str(exc), "symbol": symbol}
    except Exception as exc:  # noqa: BLE001
        log.warning("Finnhub quote error for %s: %s", symbol, exc)
        return {"error": str(exc), "symbol": symbol}


async def get_quotes(symbols: List[str]) -> List[Dict[str, Any]]:
    """Return quotes for a list of symbols."""
    import asyncio

    return await asyncio.gather(*[get_quote(s) for s in symbols])


async def get_option_chain(symbol: str) -> Dict[str, Any]:
    """Return option chain for *symbol*.

    Finnhub option chain is available on paid tiers.  On free tier the
    endpoint returns HTTP 403 or an empty payload.  We handle both cases
    gracefully and return a structured response so the UI can display a
    friendly fallback message.
    """
    if not settings.finnhub_api_key:
        return {"error": "FINNHUB_API_KEY not configured", "symbol": symbol}

    cache_key = f"options:{symbol}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_BASE}/stock/option-chain",
                params={"symbol": symbol},
                headers=_headers(),
            )
            if r.status_code == 403:
                result: Dict[str, Any] = {
                    "symbol": symbol,
                    "unavailable": True,
                    "message": (
                        "Options chain data requires a Finnhub paid plan. "
                        "Upgrade at https://finnhub.io/pricing to enable this feature."
                    ),
                }
                cache.set(cache_key, result, ttl=_OPTION_TTL)
                return result
            r.raise_for_status()
            data = r.json()
            if not data or not data.get("data"):
                result = {
                    "symbol": symbol,
                    "unavailable": True,
                    "message": (
                        "No options data returned for this symbol. "
                        "Options may not be available on your Finnhub plan."
                    ),
                }
                cache.set(cache_key, result, ttl=_OPTION_TTL)
                return result
            data["symbol"] = symbol
            cache.set(cache_key, data, ttl=_OPTION_TTL)
            return data
    except httpx.HTTPStatusError as exc:
        log.warning("Finnhub options HTTP error for %s: %s", symbol, exc)
        return {"error": str(exc), "symbol": symbol, "unavailable": True}
    except Exception as exc:  # noqa: BLE001
        log.warning("Finnhub options error for %s: %s", symbol, exc)
        return {"error": str(exc), "symbol": symbol, "unavailable": True}


async def search_symbols(query: str) -> List[Dict[str, Any]]:
    """Search for symbols matching *query*."""
    if not settings.finnhub_api_key:
        return []
    cache_key = f"search:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_BASE}/search",
                params={"q": query},
                headers=_headers(),
            )
            r.raise_for_status()
            results = r.json().get("result", [])
            cache.set(cache_key, results, ttl=300)
            return results
    except Exception as exc:  # noqa: BLE001
        log.warning("Finnhub search error: %s", exc)
        return []
