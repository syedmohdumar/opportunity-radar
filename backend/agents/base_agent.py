"""
Base Agent class for all data ingestion agents.
Each agent is responsible for fetching data from a specific source,
normalizing it, and storing it as MarketEvents.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import MarketEvent
import uuid

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all data ingestion agents."""

    def __init__(self, name: str, session: AsyncSession):
        self.name = name
        self.session = session
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch raw data from the source. Returns list of raw event dicts."""
        pass

    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw data into a standard MarketEvent format."""
        pass

    async def run(self) -> List[MarketEvent]:
        """Execute the agent: fetch, normalize, store."""
        self.logger.info(f"[{self.name}] Starting data ingestion...")
        events = []
        try:
            raw_items = await self.fetch_data()
            self.logger.info(f"[{self.name}] Fetched {len(raw_items)} raw items")

            for item in raw_items:
                try:
                    normalized = self.normalize(item)
                    event = MarketEvent(
                        id=str(uuid.uuid4()),
                        event_type=normalized["event_type"],
                        symbol=normalized.get("symbol"),
                        title=normalized["title"],
                        description=normalized.get("description"),
                        data=normalized.get("data", {}),
                        source=normalized.get("source", self.name),
                        event_date=normalized.get("event_date", datetime.utcnow()),
                    )
                    self.session.add(event)
                    events.append(event)
                except Exception as e:
                    self.logger.warning(f"[{self.name}] Failed to process item: {e}")
                    continue

            await self.session.commit()
            self.logger.info(f"[{self.name}] Stored {len(events)} events")
        except Exception as e:
            self.logger.error(f"[{self.name}] Agent run failed: {e}")
            await self.session.rollback()

        return events
