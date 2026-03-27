"""
Orchestrator Service
Coordinates all agents and the signal detection engine.
Runs on a schedule or on-demand.
"""
import asyncio
import logging
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.corporate_filings_agent import CorporateFilingsAgent
from backend.agents.bulk_block_deals_agent import BulkBlockDealsAgent
from backend.agents.insider_trades_agent import InsiderTradesAgent
from backend.agents.quarterly_results_agent import QuarterlyResultsAgent
from backend.agents.regulatory_agent import RegulatoryAgent
from backend.agents.ipo_agent import IPOAgent
from backend.services.signal_engine import SignalDetectionEngine
from backend.models.models import MarketEvent, Signal

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates data ingestion agents and signal detection."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.agents = [
            CorporateFilingsAgent(session),
            BulkBlockDealsAgent(session),
            InsiderTradesAgent(session),
            QuarterlyResultsAgent(session),
            RegulatoryAgent(session),
            IPOAgent(session),
        ]
        self.signal_engine = SignalDetectionEngine(session)

    async def run_full_scan(self) -> Dict:
        """Run all agents and then detect signals."""
        logger.info("Starting full market scan...")
        all_events: List[MarketEvent] = []
        agent_results = {}

        for agent in self.agents:
            try:
                events = await agent.run()
                all_events.extend(events)
                agent_results[agent.name] = {
                    "status": "success",
                    "events_count": len(events),
                }
                logger.info(f"Agent {agent.name}: {len(events)} events")
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                agent_results[agent.name] = {
                    "status": "error",
                    "error": str(e),
                }

        # Run signal detection on all collected events
        signals: List[Signal] = []
        if all_events:
            # Prioritize: insider trades and filings with keywords are most signal-rich
            # Send max 60 events in 3 batches to respect Gemini free tier rate limits
            priority_events = self._prioritize_events(all_events, max_events=30)
            logger.info(f"Prioritized {len(priority_events)} events from {len(all_events)} total for AI analysis")

            for i in range(0, len(priority_events), 5):
                batch = priority_events[i : i + 5]
                batch_signals = await self.signal_engine.analyze_events(batch)
                signals.extend(batch_signals)
                # Rate limit: wait 10 seconds between batches for Groq free tier
                if i + 5 < len(priority_events):
                    await asyncio.sleep(10)

        result = {
            "total_events": len(all_events),
            "total_signals": len(signals),
            "agent_results": agent_results,
            "signals": [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "title": s.title,
                    "category": s.signal_category,
                    "confidence": s.confidence_score,
                    "impact": s.potential_impact,
                }
                for s in signals
            ],
        }

        logger.info(f"Full scan complete: {len(all_events)} events → {len(signals)} signals")
        return result

    @staticmethod
    def _prioritize_events(events: List[MarketEvent], max_events: int = 60) -> List[MarketEvent]:
        """Pick the most signal-rich events for AI analysis."""
        high_priority_keywords = [
            "promoter", "insider", "bulk", "block", "merger", "acquisition",
            "buyback", "bonus", "split", "demerger", "rights", "dividend",
            "result", "quarterly", "regulatory", "sebi",
            "ipo", "irregularity", "red flag", "listing", "overpricing",
        ]

        def score(event):
            s = 0
            text = ((event.title or "") + " " + (event.description or "")).lower()
            for kw in high_priority_keywords:
                if kw in text:
                    s += 2
            # Insider trades are high priority
            if event.event_type == "insider_trade":
                s += 3
                data = event.data or {}
                if data.get("is_promoter"):
                    s += 5
            # Bulk/block deals
            if "deal" in (event.event_type or ""):
                s += 3
            # Filing subtypes
            if event.event_type and event.event_type.startswith("filing_") and event.event_type != "filing_general":
                s += 2
            # IPOs with irregularities are high priority
            if event.event_type == "ipo_issue":
                s += 3
                data = event.data or {}
                s += data.get("red_flag_count", 0) * 3
                s += data.get("irregularity_count", 0) * 3
            return s

        scored = sorted(events, key=score, reverse=True)
        return scored[:max_events]

    async def run_single_agent(self, agent_name: str) -> Dict:
        """Run a specific agent by name."""
        agent_map = {a.name: a for a in self.agents}
        agent = agent_map.get(agent_name)
        if not agent:
            return {"error": f"Unknown agent: {agent_name}"}

        events = await agent.run()
        signals = await self.signal_engine.analyze_events(events) if events else []

        return {
            "agent": agent_name,
            "events_count": len(events),
            "signals_count": len(signals),
            "signals": [
                {"id": s.id, "symbol": s.symbol, "title": s.title, "confidence": s.confidence_score}
                for s in signals
            ],
        }
