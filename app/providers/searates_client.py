"""SeaRates Logistics Explorer API client – shipping rates."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app import cache
from app.config import settings

log = logging.getLogger(__name__)

_SHIPPING_TTL = 600  # 10 minutes


def _base() -> str:
    return settings.searates_base_url.rstrip("/")


async def get_rates(
    origin_port: str,
    destination_port: str,
    container_type: str = "20DC",
    cargo_weight: Optional[float] = None,
) -> Dict[str, Any]:
    """Fetch shipping rates from SeaRates Logistics Explorer API.

    Parameters
    ----------
    origin_port:      UN/LOCODE or port name, e.g. "USNYC"
    destination_port: UN/LOCODE or port name, e.g. "CNSHA"
    container_type:   Container type code: 20DC, 40DC, 40HC, etc.
    cargo_weight:     Optional cargo weight in kg
    """
    if not settings.searates_api_key:
        return {
            "error": "SEARATES_API_KEY not configured",
            "rates": [],
        }

    cache_key = f"shipping:{origin_port}:{destination_port}:{container_type}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params: Dict[str, Any] = {
        "api_key": settings.searates_api_key,
        "origin": origin_port,
        "destination": destination_port,
        "container_type": container_type,
    }
    if cargo_weight is not None:
        params["weight"] = cargo_weight

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"{_base()}/explorer/v3/rates",
                params=params,
            )
            if r.status_code == 401:
                return {
                    "error": "Invalid or missing SEARATES_API_KEY. "
                    "Register at https://www.searates.com/reference/logistics-explorer/",
                    "rates": [],
                }
            if r.status_code == 404:
                return {
                    "error": "No routes found for the given origin/destination.",
                    "rates": [],
                }
            r.raise_for_status()
            data = r.json()
            result = _normalise(data, origin_port, destination_port, container_type)
            cache.set(cache_key, result, ttl=_SHIPPING_TTL)
            return result
    except httpx.HTTPStatusError as exc:
        log.warning("SeaRates HTTP error: %s", exc)
        return {"error": str(exc), "rates": []}
    except Exception as exc:  # noqa: BLE001
        log.warning("SeaRates error: %s", exc)
        return {"error": str(exc), "rates": []}


def _normalise(
    raw: Any,
    origin: str,
    destination: str,
    container_type: str,
) -> Dict[str, Any]:
    """Normalise SeaRates response into a consistent structure.

    The SeaRates Logistics Explorer API can return varied structures
    depending on the plan.  We extract a flat list of rate entries.
    """
    rates: List[Dict[str, Any]] = []

    # Handle list response
    if isinstance(raw, list):
        for item in raw:
            rates.append(_extract_rate(item))
    elif isinstance(raw, dict):
        # Common patterns in the API response
        for key in ("rates", "data", "results", "quotes"):
            if key in raw and isinstance(raw[key], list):
                for item in raw[key]:
                    rates.append(_extract_rate(item))
                break
        else:
            # Single rate object
            rates.append(_extract_rate(raw))

    return {
        "origin": origin,
        "destination": destination,
        "container_type": container_type,
        "rates": rates,
    }


def _extract_rate(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw rate dict to a standardised schema."""
    return {
        "carrier": item.get("carrier") or item.get("scac") or item.get("carrier_name", ""),
        "transit_days": item.get("transit_time") or item.get("transit_days") or item.get("days"),
        "total_price": item.get("total") or item.get("price") or item.get("total_price"),
        "currency": item.get("currency", "USD"),
        "valid_until": item.get("valid_until") or item.get("expiry") or item.get("validity_to"),
        "service": item.get("service") or item.get("service_name", ""),
        "raw": item,
    }


CONTAINER_TYPES: List[Dict[str, str]] = [
    {"code": "20DC", "label": "20' Dry Container"},
    {"code": "40DC", "label": "40' Dry Container"},
    {"code": "40HC", "label": "40' High Cube"},
    {"code": "20RF", "label": "20' Reefer"},
    {"code": "40RF", "label": "40' Reefer"},
    {"code": "20OT", "label": "20' Open Top"},
    {"code": "40OT", "label": "40' Open Top"},
]
