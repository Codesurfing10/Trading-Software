"""Shipping routes – rates via SeaRates Logistics Explorer API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.providers import searates_client

router = APIRouter(prefix="/shipping", tags=["shipping"])


@router.get("/rates")
async def get_rates(
    origin: str = Query(..., description="Origin port UN/LOCODE, e.g. USNYC"),
    destination: str = Query(..., description="Destination port UN/LOCODE, e.g. CNSHA"),
    container_type: str = Query(default="20DC", description="Container type code"),
    weight: Optional[float] = Query(default=None, description="Cargo weight in kg"),
):
    """Fetch shipping rates between *origin* and *destination*."""
    return await searates_client.get_rates(
        origin_port=origin.upper(),
        destination_port=destination.upper(),
        container_type=container_type.upper(),
        cargo_weight=weight,
    )


@router.get("/containers")
async def list_container_types():
    """Return the list of supported container type codes."""
    return {"container_types": searates_client.CONTAINER_TYPES}
