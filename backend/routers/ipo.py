"""
IPO API Router — Upcoming IPOs, irregularity detection, and AI analysis.
"""
import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from groq import Groq
from backend.database import get_db
from backend.models.models import MarketEvent
from backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ipo", tags=["ipo"])


def _get_groq_client():
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


def _analyze_ipo_with_ai(client, ipo_data: dict) -> dict:
    """Use Groq/Llama to generate IPO analysis with positives, negatives, and return potential."""
    prompt = f"""You are an expert Indian stock market IPO analyst. Analyze this IPO and provide a detailed assessment.

IPO Details:
{json.dumps(ipo_data, indent=2, default=str)}

Return JSON with these exact keys:
{{
    "verdict": "Subscribe|Neutral|Avoid",
    "verdict_color": "green|yellow|red",
    "return_potential": "Expected listing gain/loss % range, e.g. '+15% to +25%'",
    "risk_level": "Low|Medium|High|Very High",
    "positives": ["list of 3-5 positive factors about this IPO"],
    "negatives": ["list of 2-4 risk factors or red flags"],
    "ai_summary": "2-3 sentence plain English summary of the IPO opportunity for retail investors",
    "key_metrics": {{
        "valuation_assessment": "Fairly Valued|Overvalued|Undervalued|Highly Overvalued",
        "sector_outlook": "Positive|Neutral|Negative",
        "promoter_track_record": "Strong|Average|Weak|Unknown"
    }}
}}

Only output valid JSON. Be honest — flag real risks. Indian retail investors depend on this analysis.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert IPO analyst for the Indian stock market. Always return valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"IPO AI analysis failed: {e}")
        return {
            "verdict": "Review Pending",
            "verdict_color": "yellow",
            "return_potential": "N/A",
            "risk_level": "Unknown",
            "positives": ["Data available for manual review"],
            "negatives": ["AI analysis temporarily unavailable"],
            "ai_summary": "AI analysis could not be generated at this time. Please review the IPO details manually.",
            "key_metrics": {},
        }


@router.get("/")
async def get_ipos(
    search: Optional[str] = Query(None, description="Search IPO by company name"),
    db: AsyncSession = Depends(get_db),
):
    """Get all IPO events with basic info. Optionally search by name."""
    query = select(MarketEvent).where(
        MarketEvent.event_type == "ipo_issue"
    ).order_by(desc(MarketEvent.ingested_at)).limit(50)

    result = await db.execute(query)
    events = list(result.scalars().all())

    ipos = []
    for e in events:
        data = e.data or {}
        company_name = data.get("company_name", e.symbol or "Unknown")

        # Apply search filter
        if search and search.lower() not in company_name.lower() and search.lower() not in (e.symbol or "").lower():
            continue

        red_flags = data.get("red_flags", []) + data.get("irregularities", [])

        ipos.append({
            "id": e.id,
            "symbol": e.symbol,
            "company_name": company_name,
            "category": data.get("category", "mainboard"),
            "price_band": data.get("price_band", "N/A"),
            "issue_size": data.get("issue_size", data.get("issue_size_cr", "N/A")),
            "open_date": data.get("open_date", ""),
            "close_date": data.get("close_date", ""),
            "listing_date": data.get("listing_date", ""),
            "listing_price": data.get("listing_price", ""),
            "status": data.get("status", ""),
            "subscription_times": data.get("subscription_times", ""),
            "red_flags": red_flags,
            "red_flag_count": len(red_flags),
            "description": e.description or "",
            "source": e.source,
        })

    return {"count": len(ipos), "ipos": ipos}


@router.get("/analyze/{ipo_id}")
async def analyze_ipo(ipo_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed AI analysis for a specific IPO."""
    result = await db.execute(
        select(MarketEvent).where(MarketEvent.id == ipo_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        return {"error": "IPO not found"}

    data = event.data or {}
    company_name = data.get("company_name", event.symbol or "Unknown")

    ipo_info = {
        "company_name": company_name,
        "symbol": event.symbol,
        "category": data.get("category", "mainboard"),
        "price_band": data.get("price_band", "N/A"),
        "issue_size": data.get("issue_size", data.get("issue_size_cr", "N/A")),
        "open_date": data.get("open_date", ""),
        "close_date": data.get("close_date", ""),
        "listing_date": data.get("listing_date", ""),
        "listing_price": data.get("listing_price", ""),
        "status": data.get("status", ""),
        "subscription_times": data.get("subscription_times", ""),
        "red_flags": data.get("red_flags", []) + data.get("irregularities", []),
        "description": event.description or "",
    }

    client = _get_groq_client()
    analysis = _analyze_ipo_with_ai(client, ipo_info)

    return {
        "ipo": ipo_info,
        "analysis": analysis,
    }


@router.get("/search-analyze")
async def search_and_analyze_ipo(
    query: str = Query(..., description="Company name or symbol to search"),
    db: AsyncSession = Depends(get_db),
):
    """Search for an IPO by name and return AI analysis."""
    result = await db.execute(
        select(MarketEvent).where(
            MarketEvent.event_type == "ipo_issue"
        ).order_by(desc(MarketEvent.ingested_at)).limit(100)
    )
    events = list(result.scalars().all())

    # Find the best match
    query_lower = query.lower()
    match = None
    for e in events:
        data = e.data or {}
        company_name = data.get("company_name", e.symbol or "")
        if query_lower in company_name.lower() or query_lower in (e.symbol or "").lower():
            match = e
            break

    if not match:
        return {"error": f"No IPO found matching '{query}'. Try running a scan first to fetch latest IPO data."}

    data = match.data or {}
    company_name = data.get("company_name", match.symbol or "Unknown")

    ipo_info = {
        "company_name": company_name,
        "symbol": match.symbol,
        "category": data.get("category", "mainboard"),
        "price_band": data.get("price_band", "N/A"),
        "issue_size": data.get("issue_size", data.get("issue_size_cr", "N/A")),
        "open_date": data.get("open_date", ""),
        "close_date": data.get("close_date", ""),
        "listing_date": data.get("listing_date", ""),
        "listing_price": data.get("listing_price", ""),
        "status": data.get("status", ""),
        "subscription_times": data.get("subscription_times", ""),
        "red_flags": data.get("red_flags", []) + data.get("irregularities", []),
        "description": match.description or "",
    }

    client = _get_groq_client()
    analysis = _analyze_ipo_with_ai(client, ipo_info)

    return {
        "ipo": ipo_info,
        "analysis": analysis,
    }
