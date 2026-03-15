"""Open-Meteo client – free weather API, no key required."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app import cache
from app.config import settings

log = logging.getLogger(__name__)

_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_WEATHER_TTL = 600  # 10 minutes

_WMO_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Violent showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ hail",
    99: "Thunderstorm w/ heavy hail",
}


def _wmo_label(code: Optional[int]) -> str:
    if code is None:
        return "Unknown"
    return _WMO_CODES.get(code, f"Weather code {code}")


async def _resolve_coords(city: str) -> Optional[Dict[str, Any]]:
    """Return {lat, lon, name, country} for *city* or None on failure."""
    cache_key = f"geo:{city}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(_GEO_URL, params={"name": city, "count": 1})
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return None
            hit = results[0]
            data = {
                "lat": hit["latitude"],
                "lon": hit["longitude"],
                "name": hit.get("name", city),
                "country": hit.get("country", ""),
            }
            cache.set(cache_key, data, ttl=86400)
            return data
    except Exception as exc:  # noqa: BLE001
        log.warning("Open-Meteo geocoding error for %s: %s", city, exc)
        return None


async def get_weather(
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> Dict[str, Any]:
    """Return current weather + 7-day daily forecast for the given location."""
    # Resolve coordinates
    location_name = city or settings.weather_city
    resolved_lat = lat or settings.weather_lat
    resolved_lon = lon or settings.weather_lon

    if city:
        geo = await _resolve_coords(city)
        if geo:
            resolved_lat = geo["lat"]
            resolved_lon = geo["lon"]
            location_name = f"{geo['name']}, {geo['country']}"
        else:
            return {"error": f"Could not find coordinates for city: {city}"}

    cache_key = f"weather:{resolved_lat:.4f}:{resolved_lon:.4f}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        "latitude": resolved_lat,
        "longitude": resolved_lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "wind_speed_10m",
            "weathercode",
        ],
        "daily": [
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ],
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
        "forecast_days": 7,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(_FORECAST_URL, params=params)
            r.raise_for_status()
            raw = r.json()

        current = raw.get("current", {})
        daily = raw.get("daily", {})

        # Build daily forecast list
        forecast = []
        dates = daily.get("time", [])
        for i, date in enumerate(dates):
            forecast.append(
                {
                    "date": date,
                    "code": daily.get("weathercode", [None] * len(dates))[i],
                    "description": _wmo_label(
                        daily.get("weathercode", [None] * len(dates))[i]
                    ),
                    "temp_max": daily.get("temperature_2m_max", [None] * len(dates))[i],
                    "temp_min": daily.get("temperature_2m_min", [None] * len(dates))[i],
                    "precipitation": daily.get("precipitation_sum", [None] * len(dates))[
                        i
                    ],
                }
            )

        result = {
            "location": location_name,
            "lat": resolved_lat,
            "lon": resolved_lon,
            "current": {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "code": current.get("weathercode"),
                "description": _wmo_label(current.get("weathercode")),
            },
            "forecast": forecast,
        }
        cache.set(cache_key, result, ttl=_WEATHER_TTL)
        return result
    except Exception as exc:  # noqa: BLE001
        log.warning("Open-Meteo forecast error: %s", exc)
        return {"error": str(exc)}
