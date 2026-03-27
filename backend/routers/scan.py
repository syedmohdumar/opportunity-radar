"""
Scan API Router — Trigger agent scans and deep analysis.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.orchestrator import Orchestrator
from backend.services.signal_engine import SignalDetectionEngine

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("/full")
async def trigger_full_scan(db: AsyncSession = Depends(get_db)):
    """Trigger a full scan across all data sources."""
    orchestrator = Orchestrator(db)
    result = await orchestrator.run_full_scan()
    return result


@router.post("/agent/{agent_name}")
async def trigger_agent_scan(agent_name: str, db: AsyncSession = Depends(get_db)):
    """Trigger a scan for a specific agent."""
    orchestrator = Orchestrator(db)
    result = await orchestrator.run_single_agent(agent_name)
    return result


@router.get("/deep-analysis/{symbol}")
async def deep_analysis(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get cross-event deep analysis for a specific stock."""
    engine = SignalDetectionEngine(db)
    result = await engine.get_cross_event_analysis(symbol.upper())
    if result is None:
        return {"error": f"No recent events found for {symbol.upper()}"}
    return {"symbol": symbol.upper(), "analysis": result}


@router.get("/agents")
async def list_agents():
    """List available data ingestion agents."""
    return {
        "agents": [
            {"name": "corporate_filings", "description": "Corporate announcements, board meetings, filings"},
            {"name": "bulk_block_deals", "description": "Bulk and block deals on NSE"},
            {"name": "insider_trades", "description": "Insider/promoter trading (SAST/PIT)"},
            {"name": "quarterly_results", "description": "Quarterly financial results"},
            {"name": "regulatory", "description": "SEBI circulars and regulatory updates"},
        ]
    }
