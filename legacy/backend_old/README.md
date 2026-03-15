# VNStock FastAPI Backend

This backend now uses `vnstock` as the primary data provider and is compatible with the existing Vue frontend.

It also persists successful API payloads to a local SQLite cache and automatically falls back to the latest cached payload when live `vnstock` calls fail.

## Features

- Startup snapshot warm-up for VN30 latest close prices
- Persistent SQLite cache for API responses (`backend/data/vnstock_cache.db` by default)
- OHLCV history endpoint
- Technical analysis endpoint (SMA/EMA/RSI/MACD/Bollinger/Stochastic/ATR/OBV)
- Company overview and financial data
- Aggregated market news and events
- Compatibility endpoints for existing frontend flows

## 1) Install dependencies

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Run locally

```bash
uvicorn stock_api_server:app --host 0.0.0.0 --port 8000 --reload
```

Windows shortcut via npm script:

```bash
npm --prefix c:\Users\Lenovo\Downloads\tailadmin-vuejs-1.0.0\backend run dev:python:venv
```

## 3) Optional environment variables

- `VNSTOCK_API_KEY` (or `VNAI_API_KEY`) - your vnstock community/sponsor API key
- `VNSTOCK_QUOTE_SOURCE` (default: `kbs`)
- `VNSTOCK_COMPANY_SOURCE` (default: `KBS`)
- `VNSTOCK_FINANCE_SOURCE` (default: `kbs`)
- `VNSTOCK_LISTING_SOURCE` (default: `kbs`)
- `ENABLE_STARTUP_WARMUP` (default: `true`)
- `VNSTOCK_STARTUP_SYMBOLS` (comma-separated symbols)
- `MAX_STARTUP_SYMBOLS` (default: `8`)
- `DEFAULT_HISTORY_LIMIT` (default: `365`)
- `SNAPSHOT_REFRESH_SECONDS` (default: `900`)
- `MARKET_REFRESH_SECONDS` (default: `180`)
- `NEWS_REFRESH_SECONDS` (default: `300`)
- `EVENTS_REFRESH_SECONDS` (default: `600`)
- `VNSTOCK_CACHE_DB` (optional absolute/relative SQLite file path)

Example (PowerShell):

```powershell
$env:VNSTOCK_API_KEY = "your_api_key_here"
# Optional for strict community rate control
$env:ENABLE_STARTUP_WARMUP = "true"
$env:MAX_STARTUP_SYMBOLS = "8"
```

## 4) Main API endpoints

- `GET /api/health`
- `GET /api/stocks`
- `GET /api/stocks/snapshots`
- `GET /api/stocks/{symbol}/overview`
- `GET /api/stocks/{symbol}/history`
- `GET /api/stocks/{symbol}/technical`
- `GET /api/stocks/{symbol}/financials`
- `GET /api/market-indices`
- `GET /api/stocks/{symbol}/news`
- `GET /api/stocks/{symbol}/events`
- `GET /api/news`
- `GET /api/events`
- `POST /api/dnse/save-quotes` (persists realtime quotes into snapshot cache)

Most data endpoints include response metadata:

- `source`: `live`, `live_or_cache`, `database`, `empty`, or `default`
- `last_synced_at`: server-side cache write time for this payload
