"""FastAPI entrypoint for the Trading Platform."""

from __future__ import annotations

import logging
import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import dashboard, markets, news, options, shipping, weather

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)

app = FastAPI(
    title="Trading Platform",
    description=(
        "A modular trading platform dashboard with real-time stock quotes, "
        "options data, weather, shipping rates, and financial news."
    ),
    version="1.0.0",
)

# Static files
_STATIC_DIR = pathlib.Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Routers
app.include_router(dashboard.router)
app.include_router(markets.router)
app.include_router(options.router)
app.include_router(weather.router)
app.include_router(shipping.router)
app.include_router(news.router)
