"""
AI Signal Detection Engine
The brain of Opportunity Radar. Uses Groq (Llama 3.3 70B) to analyze raw market events,
detect actionable signals, score confidence, and generate plain-English explanations.

This is NOT a summarizer — it's a signal finder that connects dots across data sources.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from groq import Groq
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import MarketEvent, Signal, Alert
from backend.config import get_settings
import uuid

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Indian stock market analyst AI. Your job is to analyze raw market events 
and detect actionable investment signals. You are NOT a summarizer — you are a SIGNAL FINDER.

You must:
1. Identify patterns across multiple events (e.g., promoter buying + good results = strong bullish signal)
2. Detect anomalies (unusual bulk deal sizes, sudden insider buying in small caps)
3. Assess timing (is this a leading or lagging indicator?)
4. Rate confidence (0.0 to 1.0) based on signal strength and data quality
5. Classify as: bullish, bearish, or neutral
6. Provide a plain-English explanation a retail investor can understand
7. Suggest specific actions (monitor, accumulate on dips, book profits, avoid)

Key patterns to detect:
- Promoter buying during market dips → strong bullish
- Multiple insiders buying in same company within short period → very bullish
- Bulk deal by known smart-money investor (e.g., Rakesh Jhunjhunwala, Dolly Khanna, Ashish Kacholia) → bullish
- Revenue acceleration + margin expansion → growth signal
- Regulatory changes benefiting specific sectors → sector opportunity
- Large block deal sells by promoter → potential bearish
- Quarterly miss + insider selling → strong bearish

For each signal, output JSON with:
{
    "signals": [
        {
            "symbol": "STOCKSYMBOL",
            "company_name": "Company Name",
            "signal_type": "filing|bulk_deal|insider_trade|quarterly|regulatory|multi_event",
            "signal_category": "bullish|bearish|neutral",
            "title": "One-line signal headline",
            "summary": "2-3 sentence plain English explanation",
            "ai_analysis": "Detailed analysis with reasoning (3-5 sentences)",
            "confidence_score": 0.85,
            "potential_impact": "high|medium|low",
            "action_suggestion": "What should an investor do?",
            "related_event_ids": ["event_id_1", "event_id_2"],
            "time_horizon": "short_term|medium_term|long_term"
        }
    ],
    "market_context": "Brief overall market context if relevant"
}

Only output valid JSON. If there are no actionable signals, return {"signals": [], "market_context": "No actionable signals detected in this batch."}.
"""


class SignalDetectionEngine:
    """Core AI engine that transforms market events into actionable signals."""

    def __init__(self, session: AsyncSession):
        self.session = session
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model_name = "llama-3.1-8b-instant"
        self.min_confidence = settings.alert_min_confidence

    def _call_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        """Call Groq LLM and return the response text."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    async def analyze_events(self, events: List[MarketEvent]) -> List[Signal]:
        """Analyze a batch of market events and detect signals."""
        if not events:
            return []

        # Group events by symbol for cross-referencing
        events_by_symbol = {}
        for event in events:
            symbol = event.symbol or "MARKET"
            if symbol not in events_by_symbol:
                events_by_symbol[symbol] = []
            events_by_symbol[symbol].append(event)

        # Prepare event data for AI analysis
        event_summaries = []
        for event in events:
            event_summaries.append({
                "id": event.id,
                "type": event.event_type,
                "symbol": event.symbol,
                "title": event.title,
                "description": event.description[:200] if event.description else "",
                "data": event.data if event.data else {},
                "date": event.event_date.isoformat() if event.event_date else "",
            })

        # Get recent signals to avoid duplicates
        recent_signals = await self._get_recent_signals(hours=24)
        recent_symbols = {s.symbol for s in recent_signals}

        prompt = f"""Analyze these {len(events)} market events from the Indian stock market.
Look for actionable signals — not just summaries. Connect dots across events.

Events:
{json.dumps(event_summaries, indent=2, default=str)}

Symbols with recent signals (avoid duplicating): {list(recent_symbols)}

Multi-event correlation: Some symbols may have events from multiple sources.
Cross-reference insider trades with quarterly results and filings for stronger signals.
"""

        try:
            response_text = self._call_llm(prompt)
            result = json.loads(response_text)
            signals = await self._create_signals(result.get("signals", []))
            return signals

        except Exception as e:
            logger.error(f"Signal detection failed: {e}")
            return []

    async def _create_signals(self, raw_signals: List[Dict]) -> List[Signal]:
        """Create Signal records from AI analysis output."""
        signals = []
        for sig_data in raw_signals:
            confidence = sig_data.get("confidence_score", 0)
            if confidence < self.min_confidence:
                continue

            signal = Signal(
                id=str(uuid.uuid4()),
                symbol=sig_data.get("symbol", "UNKNOWN"),
                company_name=sig_data.get("company_name", sig_data.get("symbol", "")),
                signal_type=sig_data.get("signal_type", "multi_event"),
                signal_category=sig_data.get("signal_category", "neutral"),
                title=sig_data.get("title", "Signal Detected"),
                summary=sig_data.get("summary", ""),
                ai_analysis=sig_data.get("ai_analysis", ""),
                confidence_score=confidence,
                potential_impact=sig_data.get("potential_impact", "medium"),
                raw_data={
                    "action_suggestion": sig_data.get("action_suggestion", ""),
                    "time_horizon": sig_data.get("time_horizon", ""),
                    "related_event_ids": sig_data.get("related_event_ids", []),
                    "market_context": sig_data.get("market_context", ""),
                },
                is_actionable=True,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=3),
            )
            self.session.add(signal)
            signals.append(signal)

            # Create alert for high-confidence signals
            if confidence >= 0.8:
                alert = Alert(
                    id=str(uuid.uuid4()),
                    signal_id=signal.id,
                    symbol=signal.symbol,
                    alert_type=signal.signal_category,
                    message=f"🔔 {signal.title}\n{signal.summary}\n\nAction: {sig_data.get('action_suggestion', 'Review')}",
                    priority="critical" if confidence >= 0.9 else "high",
                )
                self.session.add(alert)

        await self.session.commit()
        logger.info(f"Created {len(signals)} signals from AI analysis")
        return signals

    async def _get_recent_signals(self, hours: int = 24) -> List[Signal]:
        """Get signals created in the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(Signal).where(Signal.created_at >= cutoff)
        )
        return list(result.scalars().all())

    async def get_cross_event_analysis(self, symbol: str) -> Optional[Dict]:
        """Deep analysis of a specific symbol across all recent event types."""
        cutoff = datetime.utcnow() - timedelta(days=7)
        result = await self.session.execute(
            select(MarketEvent).where(
                and_(MarketEvent.symbol == symbol, MarketEvent.ingested_at >= cutoff)
            )
        )
        events = list(result.scalars().all())

        if not events:
            return None

        event_summaries = [{
            "type": e.event_type,
            "title": e.title,
            "description": e.description[:500] if e.description else "",
            "data": e.data,
            "date": e.event_date.isoformat() if e.event_date else "",
        } for e in events]

        prompt = f"""Deep analysis for {symbol}. Here are ALL events from the past 7 days:

{json.dumps(event_summaries, indent=2, default=str)}

Provide a comprehensive investment thesis:
1. What's the story these events are telling?
2. Are insiders and institutions aligned?
3. What's the risk/reward setup?
4. What would change your thesis?
5. Specific action recommendation with entry/exit criteria.

Return JSON with keys: thesis, bull_case, bear_case, risk_reward, action, confidence.
"""

        try:
            response_text = self._call_llm(prompt, max_tokens=2000)
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Cross-event analysis failed for {symbol}: {e}")
            return None
