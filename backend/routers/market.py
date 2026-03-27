"""
Market Data Router — Live index prices and market overview.
"""
import logging
import httpx
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market", tags=["market"])

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

INDICES = [
    {"symbol": "NIFTY 50", "key": "NIFTY 50"},
    {"symbol": "SENSEX", "key": "SENSEX"},
    {"symbol": "NIFTY BANK", "key": "NIFTY BANK"},
    {"symbol": "NIFTY IT", "key": "NIFTY IT"},
    {"symbol": "NIFTY MIDCAP 50", "key": "NIFTY MIDCAP 50"},
]


async def _fetch_nse_indices():
    """Try to fetch live index data from NSE."""
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            # First hit main page for cookies
            await client.get("https://www.nseindia.com", headers=NSE_HEADERS)
            resp = await client.get(
                "https://www.nseindia.com/api/allIndices",
                headers=NSE_HEADERS,
            )
            if resp.status_code == 200:
                data = resp.json()
                indices_map = {}
                for item in data.get("data", []):
                    indices_map[item.get("index", "")] = {
                        "symbol": item.get("index", ""),
                        "last": item.get("last", 0),
                        "change": item.get("percentChange", 0),
                        "change_pts": item.get("change", 0),
                        "open": item.get("open", 0),
                        "high": item.get("high", 0),
                        "low": item.get("low", 0),
                        "prev_close": item.get("previousClose", 0),
                    }
                return indices_map
    except Exception as e:
        logger.warning(f"NSE index fetch failed: {e}")
    return None


@router.get("/indices")
async def get_market_indices():
    """Get live market indices data."""
    nse_data = await _fetch_nse_indices()

    results = []
    if nse_data:
        for idx in INDICES:
            if idx["key"] in nse_data:
                results.append(nse_data[idx["key"]])

        # Add a few more popular ones if available
        extras = ["NIFTY NEXT 50", "NIFTY MIDCAP 100", "INDIA VIX", "NIFTY FINANCIAL SERVICES"]
        for e in extras:
            if e in nse_data and len(results) < 8:
                results.append(nse_data[e])

    if not results:
        # Fallback with realistic sample data
        results = [
            {"symbol": "NIFTY 50", "last": 23305.10, "change": 1.71, "change_pts": 391.85, "prev_close": 22913.25},
            {"symbol": "SENSEX", "last": 76905.51, "change": 1.63, "change_pts": 1234.07, "prev_close": 75671.44},
            {"symbol": "NIFTY BANK", "last": 51350.45, "change": 2.10, "change_pts": 1055.90, "prev_close": 50294.55},
            {"symbol": "NIFTY IT", "last": 35120.30, "change": -0.85, "change_pts": -301.20, "prev_close": 35421.50},
            {"symbol": "NIFTY MIDCAP 50", "last": 14980.75, "change": 1.45, "change_pts": 213.55, "prev_close": 14767.20},
            {"symbol": "INDIA VIX", "last": 13.42, "change": -5.20, "change_pts": -0.74, "prev_close": 14.16},
        ]

    return {"indices": results, "live": nse_data is not None}
