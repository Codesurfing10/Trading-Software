"""Dashboard route – serves the main HTML page."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.providers import (
    finnhub_client,
    open_meteo_client,
)

import pathlib

_TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main trading dashboard."""
    # Fetch initial data for server-side render
    quotes = await finnhub_client.get_quotes(settings.watchlist_symbols)
    weather = await open_meteo_client.get_weather()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "watchlist": settings.watchlist_symbols,
            "quotes": quotes,
            "weather": weather,
            "weather_city": settings.weather_city,
            "finnhub_configured": bool(settings.finnhub_api_key),
            "newsapi_configured": bool(settings.newsapi_api_key),
            "searates_configured": bool(settings.searates_api_key),
        },
    )
