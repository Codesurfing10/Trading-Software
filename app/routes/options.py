"""Options routes – option chains per symbol (best-effort on free tier)."""

from __future__ import annotations

from fastapi import APIRouter

from app.providers import finnhub_client

router = APIRouter(prefix="/options", tags=["options"])


@router.get("/{symbol}")
async def get_options(symbol: str):
    """Return option chain for *symbol*.

    On Finnhub free tier this endpoint will return an ``unavailable`` flag
    with a descriptive message instead of raising an error.
    """
    data = await finnhub_client.get_option_chain(symbol.upper())
    return data
