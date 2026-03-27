from sqlalchemy import Column, String, Float, DateTime, Integer, Text, Boolean, JSON
from sqlalchemy.sql import func
from backend.database import Base
import uuid


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    signal_type = Column(String, index=True, nullable=False)  # filing, bulk_deal, insider_trade, quarterly, regulatory
    signal_category = Column(String, nullable=False)  # bullish, bearish, neutral
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    ai_analysis = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    potential_impact = Column(String)  # high, medium, low
    source_url = Column(String)
    raw_data = Column(JSON)
    is_actionable = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    added_at = Column(DateTime, server_default=func.now())
    notes = Column(Text)


class MarketEvent(Base):
    __tablename__ = "market_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    data = Column(JSON)
    source = Column(String)
    event_date = Column(DateTime)
    ingested_at = Column(DateTime, server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String, index=True)
    symbol = Column(String, index=True, nullable=False)
    alert_type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String, default="medium")  # critical, high, medium, low
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
