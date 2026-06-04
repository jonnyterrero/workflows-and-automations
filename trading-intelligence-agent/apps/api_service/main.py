"""Trading Intelligence Agent — FastAPI application entry point."""
from __future__ import annotations

import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from packages.observability.logging import configure_logging
from packages.storage.firebase_db import create_tables, _init_firebase

configure_logging("api-service")

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
VERSION = "0.1.0"

app = FastAPI(
    title="Trading Intelligence Agent",
    description=(
        "AI-powered trading research and decision-support platform. "
        "DISCLAIMER: This system provides research signals and decision support, "
        "NOT financial advice. All outputs carry uncertainty and must not be used "
        "as sole basis for investment decisions."
    ),
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_startup_time = time.time()


@app.on_event("startup")
async def startup() -> None:
    _init_firebase()  # connect to Firestore (emulator or production)


@app.get("/health", tags=["System"])
async def health() -> dict:
    return {
        "status": "ok",
        "version": VERSION,
        "demo_mode": DEMO_MODE,
        "uptime_seconds": round(time.time() - _startup_time, 1),
    }


@app.get("/version", tags=["System"])
async def version() -> dict:
    return {"version": VERSION, "demo_mode": DEMO_MODE}


@app.get("/metrics", tags=["System"])
async def metrics() -> dict:
    return {
        "version": VERSION,
        "uptime_seconds": round(time.time() - _startup_time, 1),
        "demo_mode": DEMO_MODE,
    }


# Import and register all route modules
from apps.api_service.routes import (  # noqa: E402
    assets, market, news, signals, research, risk, backtest, admin,
)

app.include_router(assets.router, prefix="/assets", tags=["Assets"])
app.include_router(market.router, prefix="/market", tags=["Market Data"])
app.include_router(news.router, prefix="/news", tags=["News & Social"])
app.include_router(signals.router, prefix="/signals", tags=["Signals"])
app.include_router(research.router, prefix="/research", tags=["Research"])
app.include_router(risk.router, prefix="/risk", tags=["Risk"])
app.include_router(backtest.router, prefix="/backtest", tags=["Backtesting"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
