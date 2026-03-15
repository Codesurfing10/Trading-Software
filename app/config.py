"""Application settings loaded from environment variables / .env file."""

from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Finnhub
    finnhub_api_key: str = ""

    # NewsAPI
    newsapi_api_key: str = ""

    # SeaRates
    searates_api_key: str = ""
    searates_base_url: str = "https://api.searates.com"

    # Weather (Open-Meteo – no key needed)
    weather_city: str = "New York"
    weather_lat: float = 40.7128
    weather_lon: float = -74.0060

    # Watchlist
    watchlist: str = "AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA"

    @property
    def watchlist_symbols(self) -> List[str]:
        return [s.strip().upper() for s in self.watchlist.split(",") if s.strip()]


settings = Settings()
