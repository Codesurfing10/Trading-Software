# 📈 Trading Platform

A modular **FastAPI** web application that brings together real-time stock quotes, options data, weather forecasts, international shipping rates, and financial news into a single dark-themed dashboard.

![Dashboard screenshot](https://github.com/user-attachments/assets/81234160-1617-482c-af3d-f1d85bc6a273)

---

## Features

| Module | Source | API Key Required |
|---|---|---|
| **Stock Quotes** (near real-time, polling) | [Finnhub](https://finnhub.io) | ✅ Free tier |
| **Options Chain** (best-effort) | Finnhub | ✅ Paid tier; graceful fallback on free |
| **Weather & Forecast** | [Open-Meteo](https://open-meteo.com) | ❌ No key needed |
| **Shipping Rates** | [SeaRates Logistics Explorer](https://www.searates.com/reference/logistics-explorer/) | ✅ Required |
| **Financial News** | [NewsAPI](https://newsapi.org) | ✅ Free tier |

---

## Project Structure

```
app/
├── main.py                  # FastAPI entrypoint
├── config.py                # Settings loaded from environment variables
├── cache.py                 # Simple in-memory TTL cache
├── providers/
│   ├── finnhub_client.py    # Finnhub – quotes + option chains
│   ├── open_meteo_client.py # Open-Meteo – weather & forecast
│   ├── newsapi_client.py    # NewsAPI – headlines & search
│   └── searates_client.py   # SeaRates – shipping rates
├── routes/
│   ├── dashboard.py         # Main HTML dashboard
│   ├── markets.py           # GET /markets/quotes, /markets/quote/{symbol}
│   ├── options.py           # GET /options/{symbol}
│   ├── weather.py           # GET /weather
│   ├── shipping.py          # GET /shipping/rates, /shipping/containers
│   └── news.py              # GET /news/headlines, /news/search, /news/symbol/{symbol}
├── templates/
│   └── dashboard.html       # Jinja2 dashboard template
└── static/
    ├── css/main.css
    └── js/dashboard.js
```

---

## Quick Start

### 1. Clone & install dependencies

```bash
git clone https://github.com/Codesurfing10/Trading-Software.git
cd Trading-Software
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your API keys (see "Getting API Keys" below)
```

### 3. Run the app

```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000** in your browser.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Finnhub – free key at https://finnhub.io/register
FINNHUB_API_KEY=your_key_here

# NewsAPI – free key at https://newsapi.org/register
NEWSAPI_API_KEY=your_key_here

# SeaRates – register at https://www.searates.com/reference/logistics-explorer/
SEARATES_API_KEY=your_key_here
SEARATES_BASE_URL=https://api.searates.com   # default; change only if needed

# Default weather location (Open-Meteo, no key required)
WEATHER_CITY=New York
WEATHER_LAT=40.7128
WEATHER_LON=-74.0060

# Watchlist – comma-separated ticker symbols
WATCHLIST=AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA
```

The app runs with missing keys – each module displays a clear message and a link to register.

---

## Getting API Keys

### Finnhub (stock quotes & options)
1. Go to [finnhub.io/register](https://finnhub.io/register) and create a free account.
2. Copy your API key from the dashboard.
3. Set `FINNHUB_API_KEY` in `.env`.

> **Note:** The options chain endpoint requires a **paid Finnhub plan**. On the free tier the options tab displays a friendly upgrade prompt. Stock quotes work on the free tier.

### NewsAPI (financial news)
1. Go to [newsapi.org/register](https://newsapi.org/register).
2. Copy the API key shown after registration.
3. Set `NEWSAPI_API_KEY` in `.env`.

> **Note:** The free developer plan is rate-limited to 100 requests/day and does not support production deployments. Upgrade for higher limits.

### SeaRates Logistics Explorer (shipping rates)
1. Register at [searates.com](https://www.searates.com/reference/logistics-explorer/).
2. Obtain your API key from the account dashboard.
3. Set `SEARATES_API_KEY` in `.env`.

### Open-Meteo (weather)
No API key is required. Open-Meteo is a free, open-source weather service.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | HTML dashboard |
| `GET` | `/markets/quotes` | Quotes for watchlist (or `?symbols=AAPL,TSLA`) |
| `GET` | `/markets/quote/{symbol}` | Single quote |
| `GET` | `/markets/search?q=apple` | Symbol search |
| `GET` | `/options/{symbol}` | Option chain (best-effort) |
| `GET` | `/weather` | Current weather + 7-day forecast |
| `GET` | `/weather?city=London` | Weather for a specific city |
| `GET` | `/shipping/rates?origin=USNYC&destination=CNSHA&container_type=40HC` | Shipping rates |
| `GET` | `/shipping/containers` | Supported container types |
| `GET` | `/news/headlines` | Top business headlines |
| `GET` | `/news/search?q=AAPL` | News search |
| `GET` | `/news/symbol/{symbol}` | News for a ticker |
| `GET` | `/docs` | Interactive OpenAPI docs (Swagger UI) |

---

## Caching

All provider calls use a simple **in-memory TTL cache** (`app/cache.py`) to avoid hitting free-tier rate limits:

| Data | TTL |
|---|---|
| Stock quotes | 30 seconds |
| Option chains | 2 minutes |
| Weather | 10 minutes |
| Shipping rates | 10 minutes |
| News headlines | 5 minutes |

---

## Dashboard Behaviour

- **Quotes refresh automatically** every 30 seconds while the Markets tab is active.
- Quotes also refresh on-demand via the **↻ Refresh** button.
- All other modules are loaded lazily when their tab is first clicked (or when their search/lookup form is submitted).
- Error states (missing API key, network failure, no results) are displayed inline with clear messages.
