"""
Signal API Router
Endpoints for retrieving, filtering, and managing signals.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, List
from backend.database import get_db
from backend.models.models import Signal

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/")
async def get_signals(
    category: Optional[str] = Query(None, description="Filter: bullish, bearish, neutral"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    impact: Optional[str] = Query(None, description="Filter: high, medium, low"),
    hours: int = Query(72, ge=1, le=720, description="Look back N hours"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get filtered, sorted signals."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    conditions = [Signal.created_at >= cutoff, Signal.confidence_score >= min_confidence]

    if category:
        conditions.append(Signal.signal_category == category)
    if signal_type:
        conditions.append(Signal.signal_type == signal_type)
    if symbol:
        conditions.append(Signal.symbol == symbol.upper())
    if impact:
        conditions.append(Signal.potential_impact == impact)

    result = await db.execute(
        select(Signal)
        .where(and_(*conditions))
        .order_by(desc(Signal.confidence_score), desc(Signal.created_at))
        .limit(limit)
    )
    signals = result.scalars().all()

    return {
        "count": len(signals),
        "signals": [
            {
                "id": s.id,
                "symbol": s.symbol,
                "company_name": s.company_name,
                "signal_type": s.signal_type,
                "signal_category": s.signal_category,
                "title": s.title,
                "summary": s.summary,
                "ai_analysis": s.ai_analysis,
                "confidence_score": s.confidence_score,
                "potential_impact": s.potential_impact,
                "raw_data": s.raw_data,
                "is_actionable": s.is_actionable,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
    }


@router.get("/top")
async def get_top_signals(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get top actionable signals by confidence."""
    cutoff = datetime.utcnow() - timedelta(hours=48)
    result = await db.execute(
        select(Signal)
        .where(and_(Signal.created_at >= cutoff, Signal.is_actionable == True, Signal.confidence_score >= 0.75))
        .order_by(desc(Signal.confidence_score))
        .limit(limit)
    )
    signals = result.scalars().all()
    return {
        "count": len(signals),
        "signals": [
            {
                "id": s.id,
                "symbol": s.symbol,
                "company_name": s.company_name,
                "signal_category": s.signal_category,
                "title": s.title,
                "summary": s.summary,
                "confidence_score": s.confidence_score,
                "potential_impact": s.potential_impact,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
    }


@router.get("/stats")
async def get_signal_stats(db: AsyncSession = Depends(get_db)):
    """Get signal statistics."""
    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    cutoff_7d = datetime.utcnow() - timedelta(days=7)

    result_24h = await db.execute(select(Signal).where(Signal.created_at >= cutoff_24h))
    signals_24h = result_24h.scalars().all()

    result_7d = await db.execute(select(Signal).where(Signal.created_at >= cutoff_7d))
    signals_7d = result_7d.scalars().all()

    def categorize(signals):
        cats = {"bullish": 0, "bearish": 0, "neutral": 0}
        types = {}
        for s in signals:
            cats[s.signal_category] = cats.get(s.signal_category, 0) + 1
            types[s.signal_type] = types.get(s.signal_type, 0) + 1
        return cats, types

    cats_24h, types_24h = categorize(signals_24h)
    cats_7d, types_7d = categorize(signals_7d)

    return {
        "last_24h": {
            "total": len(signals_24h),
            "categories": cats_24h,
            "types": types_24h,
            "avg_confidence": sum(s.confidence_score for s in signals_24h) / len(signals_24h) if signals_24h else 0,
        },
        "last_7d": {
            "total": len(signals_7d),
            "categories": cats_7d,
            "types": types_7d,
        },
    }
