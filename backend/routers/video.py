"""
Video Engine Router — AI-generated market update video scripts and scene data.
Generates structured scene data that the frontend renders as animated visualizations.
"""
import json
import logging
import random
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from groq import Groq
from backend.database import get_db
from backend.models.models import MarketEvent, Signal
from backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["video"])


def _get_groq():
    return Groq(api_key=get_settings().groq_api_key)


# ─── Helper: fetch latest signals ───
async def _get_recent_signals(db: AsyncSession, limit: int = 20):
    result = await db.execute(
        select(Signal).order_by(desc(Signal.created_at)).limit(limit)
    )
    signals = result.scalars().all()
    return [
        {
            "symbol": s.symbol,
            "title": s.title,
            "category": s.signal_category,
            "confidence": round(s.confidence_score * 100),
            "impact": s.potential_impact,
            "type": s.signal_type,
        }
        for s in signals
    ]


# ─── Helper: fetch market events by source ───
async def _get_events_by_source(db: AsyncSession, source: str, limit: int = 30):
    result = await db.execute(
        select(MarketEvent)
        .where(MarketEvent.source == source)
        .order_by(desc(MarketEvent.ingested_at))
        .limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "symbol": e.symbol,
            "title": e.title,
            "raw": e.data if isinstance(e.data, dict) else {},
        }
        for e in events
    ]


# ═══════════════════════════════════════════════════
# 1. DAILY MARKET WRAP
# ═══════════════════════════════════════════════════
@router.get("/market-wrap")
async def market_wrap(db: AsyncSession = Depends(get_db)):
    """Generate a daily market wrap video with AI narration."""
    signals = await _get_recent_signals(db, 15)

    bullish = [s for s in signals if s["category"] == "bullish"]
    bearish = [s for s in signals if s["category"] == "bearish"]

    # Build AI script
    client = _get_groq()
    prompt = f"""You are a professional Indian stock market news anchor. Generate a concise, engaging market wrap script for a 60-second video.
    
Today's data:
- Total signals detected: {len(signals)}
- Bullish signals: {len(bullish)}
- Bearish signals: {len(bearish)}
- Top signals: {json.dumps(signals[:8], default=str)}

Generate a JSON response with exactly this structure:
{{
    "title": "Market Wrap — <date>",
    "duration": 60,
    "scenes": [
        {{
            "id": 1,
            "type": "intro",
            "duration": 8,
            "headline": "short punchy headline",
            "narration": "opening line about today's market"
        }},
        {{
            "id": 2,
            "type": "index_overview",
            "duration": 12,
            "headline": "Market Indices",
            "narration": "brief overview of how indices performed"
        }},
        {{
            "id": 3,
            "type": "top_movers",
            "duration": 15,
            "headline": "Top Movers",
            "narration": "highlight 2-3 key stocks",
            "stocks": [{{"symbol": "SYM", "move": "+5.2%", "reason": "brief reason"}}]
        }},
        {{
            "id": 4,
            "type": "signals_summary",
            "duration": 15,
            "headline": "AI Signal Radar",
            "narration": "summary of bullish vs bearish signals",
            "bullish_count": {len(bullish)},
            "bearish_count": {len(bearish)}
        }},
        {{
            "id": 5,
            "type": "outlook",
            "duration": 10,
            "headline": "Market Outlook",
            "narration": "closing outlook and what to watch"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON, no markdown fences."""

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200,
        )
        text = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
    except Exception as e:
        logger.error(f"Market wrap AI error: {e}")
        data = _fallback_market_wrap(signals, bullish, bearish)

    data["generated_at"] = datetime.utcnow().isoformat()
    data["signal_data"] = {
        "total": len(signals),
        "bullish": len(bullish),
        "bearish": len(bearish),
        "signals": signals[:10],
    }
    return data


def _fallback_market_wrap(signals, bullish, bearish):
    return {
        "title": f"Market Wrap — {datetime.utcnow().strftime('%d %b %Y')}",
        "duration": 60,
        "scenes": [
            {"id": 1, "type": "intro", "duration": 8, "headline": "Today's Market Update", "narration": f"Here's your AI-powered market briefing with {len(signals)} signals detected today."},
            {"id": 2, "type": "index_overview", "duration": 12, "headline": "Market Indices", "narration": "Markets showed mixed activity across major indices today."},
            {"id": 3, "type": "top_movers", "duration": 15, "headline": "Top Movers", "narration": "Let's look at the key stocks making moves.", "stocks": [{"symbol": s["symbol"], "move": f"{s['confidence']}% conf", "reason": s["title"][:60]} for s in signals[:3]]},
            {"id": 4, "type": "signals_summary", "duration": 15, "headline": "AI Signal Radar", "narration": f"Our AI detected {len(bullish)} bullish and {len(bearish)} bearish signals.", "bullish_count": len(bullish), "bearish_count": len(bearish)},
            {"id": 5, "type": "outlook", "duration": 10, "headline": "Market Outlook", "narration": "Stay alert for upcoming corporate events and earnings."},
        ],
    }


# ═══════════════════════════════════════════════════
# 2. RACE CHART — Stock/Sector Performance
# ═══════════════════════════════════════════════════
@router.get("/race-chart")
async def race_chart(db: AsyncSession = Depends(get_db)):
    """Generate animated race chart data from signal confidence scores."""
    signals = await _get_recent_signals(db, 30)

    # Group by symbol, aggregate confidence
    symbol_scores = {}
    for s in signals:
        sym = s["symbol"]
        if sym not in symbol_scores:
            symbol_scores[sym] = {"symbol": sym, "score": 0, "count": 0, "category": s["category"]}
        symbol_scores[sym]["score"] += s["confidence"]
        symbol_scores[sym]["count"] += 1

    ranked = sorted(symbol_scores.values(), key=lambda x: x["score"], reverse=True)[:10]

    # Generate animated frames (simulate progression over 10 frames)
    frames = []
    for frame_idx in range(10):
        progress = (frame_idx + 1) / 10
        frame = []
        for item in ranked:
            noise = random.uniform(0.7, 1.0) if frame_idx < 9 else 1.0
            frame.append({
                "symbol": item["symbol"],
                "value": round(item["score"] * progress * noise, 1),
                "category": item["category"],
            })
        frame.sort(key=lambda x: x["value"], reverse=True)
        frames.append(frame)

    return {
        "title": "Stock Signal Race",
        "subtitle": "Cumulative AI confidence scores",
        "duration": 30,
        "frame_interval": 3,
        "frames": frames,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════
# 3. SECTOR ROTATION
# ═══════════════════════════════════════════════════
@router.get("/sector-rotation")
async def sector_rotation(db: AsyncSession = Depends(get_db)):
    """Generate sector rotation heatmap from signal types."""
    signals = await _get_recent_signals(db, 40)

    # Map signal types to sectors
    sector_map = {
        "insider_trade": "Corporate Action",
        "bulk_deal": "Institutional",
        "block_deal": "Institutional",
        "quarterly_result": "Earnings",
        "filing_merger": "M&A",
        "filing_bonus": "Corporate Action",
        "filing_buyback": "Corporate Action",
        "regulatory_change": "Regulatory",
        "multi_event": "Multi-Factor",
    }

    sectors = {}
    for s in signals:
        sector = sector_map.get(s["type"], "Other")
        if sector not in sectors:
            sectors[sector] = {"name": sector, "bullish": 0, "bearish": 0, "neutral": 0, "total": 0, "avg_confidence": 0, "signals": []}
        sectors[sector]["total"] += 1
        sectors[sector][s["category"]] = sectors[sector].get(s["category"], 0) + 1
        sectors[sector]["avg_confidence"] += s["confidence"]
        sectors[sector]["signals"].append(s["symbol"])

    for sec in sectors.values():
        if sec["total"] > 0:
            sec["avg_confidence"] = round(sec["avg_confidence"] / sec["total"])
        sec["sentiment"] = "bullish" if sec["bullish"] > sec["bearish"] else "bearish" if sec["bearish"] > sec["bullish"] else "neutral"
        sec["signals"] = list(set(sec["signals"]))[:5]

    sector_list = sorted(sectors.values(), key=lambda x: x["total"], reverse=True)

    return {
        "title": "Sector Rotation Map",
        "subtitle": "Signal distribution across market sectors",
        "duration": 30,
        "sectors": sector_list,
        "total_signals": len(signals),
        "generated_at": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════
# 4. FII / DII FLOW VISUALIZATION
# ═══════════════════════════════════════════════════
@router.get("/fii-dii")
async def fii_dii_flows(db: AsyncSession = Depends(get_db)):
    """Generate FII/DII flow visualization from bulk/block deal signals."""
    events = await _get_events_by_source(db, "nse_bulk_deals", 50)
    signals = await _get_recent_signals(db, 30)

    # Categorize deals as institutional
    institutional = [s for s in signals if s["type"] in ("bulk_deal", "block_deal")]
    buying = [s for s in institutional if s["category"] == "bullish"]
    selling = [s for s in institutional if s["category"] == "bearish"]

    # Generate AI commentary
    client = _get_groq()
    prompt = f"""Generate a brief 3-sentence commentary about institutional flow activity in Indian markets.

Data:
- Total institutional signals: {len(institutional)}
- Net buying signals: {len(buying)}
- Net selling signals: {len(selling)}
- Key stocks: {[s['symbol'] for s in institutional[:5]]}

Return ONLY a JSON object:
{{"commentary": "your 3 sentences here", "sentiment": "bullish|bearish|neutral", "key_insight": "one key takeaway"}}"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        ai_data = json.loads(text)
    except Exception as e:
        logger.error(f"FII/DII AI error: {e}")
        ai_data = {
            "commentary": f"Institutional activity shows {len(buying)} buying signals and {len(selling)} selling signals across key stocks.",
            "sentiment": "bullish" if len(buying) > len(selling) else "bearish",
            "key_insight": "Monitor institutional flows for directional cues.",
        }

    # Generate flow data frames
    flow_frames = []
    for i in range(8):
        progress = (i + 1) / 8
        flow_frames.append({
            "fii_buy": round(len(buying) * 100 * progress * random.uniform(0.8, 1.2)),
            "fii_sell": round(len(selling) * 80 * progress * random.uniform(0.8, 1.2)),
            "dii_buy": round(len(buying) * 90 * progress * random.uniform(0.8, 1.2)),
            "dii_sell": round(len(selling) * 70 * progress * random.uniform(0.8, 1.2)),
        })

    return {
        "title": "FII / DII Flow Tracker",
        "subtitle": "Institutional money flow visualization",
        "duration": 30,
        "ai": ai_data,
        "summary": {
            "total_institutional": len(institutional),
            "buying": len(buying),
            "selling": len(selling),
            "stocks": [s["symbol"] for s in institutional[:8]],
        },
        "flow_frames": flow_frames,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════
# 5. IPO TRACKER
# ═══════════════════════════════════════════════════
@router.get("/ipo-tracker")
async def ipo_tracker(db: AsyncSession = Depends(get_db)):
    """Generate IPO pipeline tracker visualization."""
    result = await db.execute(
        select(MarketEvent)
        .where(MarketEvent.source.in_(["ipo_watch", "ipo_sme"]))
        .order_by(desc(MarketEvent.ingested_at))
        .limit(20)
    )
    events = result.scalars().all()

    ipos = []
    for e in events:
        raw = e.data if isinstance(e.data, dict) else {}
        ipos.append({
            "company": e.title or e.symbol,
            "symbol": e.symbol,
            "price_band": raw.get("price_band", "TBA"),
            "issue_size": raw.get("issue_size", "N/A"),
            "category": raw.get("category", "mainboard"),
            "status": raw.get("status", "upcoming"),
            "red_flags": raw.get("red_flag_count", 0),
        })

    # AI insights
    client = _get_groq()
    prompt = f"""You are an IPO market expert. Generate a 30-second narration script about the current IPO pipeline in Indian markets.

IPO data: {json.dumps(ipos[:8], default=str)}

Return ONLY valid JSON:
{{"narration": "your 4-5 sentence script", "highlight_ipo": "most interesting company name", "market_mood": "hot|warm|cool", "total_pipeline": {len(ipos)}}}"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        ai_data = json.loads(text)
    except Exception as e:
        logger.error(f"IPO tracker AI error: {e}")
        ai_data = {
            "narration": f"The IPO pipeline currently has {len(ipos)} offerings across mainboard and SME segments.",
            "highlight_ipo": ipos[0]["company"] if ipos else "N/A",
            "market_mood": "warm",
            "total_pipeline": len(ipos),
        }

    return {
        "title": "IPO Pipeline Tracker",
        "subtitle": "Upcoming & active IPO visualizer",
        "duration": 30,
        "ai": ai_data,
        "ipos": ipos,
        "generated_at": datetime.utcnow().isoformat(),
    }
