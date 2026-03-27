"""
Opportunity Radar — Main Application
AI-powered market intelligence that turns data into actionable signals.
"""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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


# ─── Serve frontend static files in production ───
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
else:
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
