"""Weather routes – current conditions and forecast via Open-Meteo."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.config import settings
from app.providers import open_meteo_client

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("")
async def get_weather(
    city: Optional[str] = Query(default=None, description="City name to look up"),
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
):
    """Return current weather and 7-day forecast.

    If no parameters are supplied the configured default location is used.
    """
    return await open_meteo_client.get_weather(
        city=city,
        lat=lat or (None if city else settings.weather_lat),
        lon=lon or (None if city else settings.weather_lon),
    )
