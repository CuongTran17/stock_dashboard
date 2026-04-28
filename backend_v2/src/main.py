"""
VNStock Intraday API V2 – application entry point.

This module is intentionally thin:
  - Creates the FastAPI app with its lifespan.
  - Registers all API routers (auth, payment, admin, portfolio, and the
    route modules extracted from the original monolithic file).

Business logic and helper functions live in:
  - src/utils.py          – pure helpers (no FastAPI, no DB)
  - src/cache.py          – DB-backed cache helpers
  - src/routes/stocks.py  – /api/stocks/* and /api/health
  - src/routes/analysis.py – /api/analysis/*
  - src/routes/market.py  – /api/market-indices/*, /api/news, /api/events
  - src/routes/internal.py – /api/dnse/*, /api/debug/*
  - src/routes/websocket.py – /api/ws/*
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.admin import router as admin_router
from src.api.auth import router as auth_router
from src.api.payment import router as payment_router
from src.api.portfolio import router as portfolio_router
from src.database.db import init_db
from src.jobs import build_lifespan
from src.routes.analysis import router as analysis_router
from src.routes.etl_status import router as etl_status_router
from src.routes.internal import router as internal_router
from src.routes.market import router as market_router
from src.routes.stocks import router as stocks_router
from src.routes.websocket import router as websocket_router
from src.services.fundamental_fetcher import fundamental_service
from src.services.vnstock_fetcher import VN30_SYMBOLS, fetcher_service
from src.utils import _env_flag, _env_int

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Preload configuration ─────────────────────────────────────────────

PRELOAD_REFERENCE_CACHE_ENABLED = _env_flag("VNSTOCK_PRELOAD_REFERENCE_CACHE", True)
PRELOAD_REFERENCE_FORCE_REFRESH = _env_flag("VNSTOCK_PRELOAD_FORCE_REFRESH", False)
PRELOAD_REFERENCE_SYMBOL_LIMIT = max(1, min(len(VN30_SYMBOLS), _env_int("VNSTOCK_PRELOAD_SYMBOL_LIMIT", 5)))

# ── Lifespan ──────────────────────────────────────────────────────────

lifespan = build_lifespan(
    init_db=init_db,
    fetcher_service=fetcher_service,
    fundamental_service=fundamental_service,
    vn30_symbols=VN30_SYMBOLS,
    preload_reference_cache_enabled=PRELOAD_REFERENCE_CACHE_ENABLED,
    preload_reference_force_refresh=PRELOAD_REFERENCE_FORCE_REFRESH,
    preload_reference_symbol_limit=PRELOAD_REFERENCE_SYMBOL_LIMIT,
)

# ── App ───────────────────────────────────────────────────────────────

app = FastAPI(title="VNStock Intraday API V2", lifespan=lifespan, version="2.0.0")

_frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
_allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
if _frontend_url and _frontend_url not in _allowed_origins:
    _allowed_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(payment_router)
app.include_router(admin_router)
app.include_router(portfolio_router)
app.include_router(stocks_router)
app.include_router(analysis_router)
app.include_router(etl_status_router)
app.include_router(market_router)
app.include_router(internal_router)
app.include_router(websocket_router)
