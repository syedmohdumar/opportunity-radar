"""
Opportunity Radar — Main Application
AI-powered market intelligence that turns data into actionable signals.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routers import signals, alerts, scan, watchlist, ipo, market, video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logging.info("Database initialized")
    yield
    # Shutdown
    logging.info("Shutting down Opportunity Radar")


app = FastAPI(
    title="Opportunity Radar",
    description="AI-powered market intelligence — turns corporate filings, bulk deals, insider trades, and quarterly results into actionable investment signals.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://*.vercel.app", "https://*.onrender.com"],
    allow_origin_regex=r"https://.*\.(vercel\.app|onrender\.com)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(signals.router)
app.include_router(alerts.router)
app.include_router(scan.router)
app.include_router(watchlist.router)
app.include_router(ipo.router)
app.include_router(market.router)
app.include_router(video.router)


@app.get("/")
async def root():
    return {
        "name": "Opportunity Radar",
        "version": "1.0.0",
        "description": "AI-powered market signal detection for Indian equities",
        "endpoints": {
            "signals": "/api/signals/",
            "alerts": "/api/alerts/",
            "scan": "/api/scan/",
            "watchlist": "/api/watchlist/",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
