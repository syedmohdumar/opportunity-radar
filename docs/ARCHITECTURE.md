# Opportunity Radar — Architecture Document

## System Overview

Opportunity Radar is a multi-agent AI system that continuously monitors Indian stock market data sources, detects actionable investment signals, and delivers them to retail investors through a real-time dashboard.

**Core Design Principle:** Signal detection, not summarization. The system connects dots across data sources that humans typically miss.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                       │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ Signal   │  │ Alerts   │  │  Deep      │  │  Stats           │  │
│  │ Feed     │  │ Panel    │  │  Analysis  │  │  Dashboard       │  │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └───────┬──────────┘  │
│       └──────────────┼──────────────┼─────────────────┘              │
│                      │    REST API  │                                │
└──────────────────────┼──────────────┼────────────────────────────────┘
                       │              │
┌──────────────────────┼──────────────┼────────────────────────────────┐
│                   BACKEND (FastAPI)  │                                │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │                    API LAYER (Routers)                         │   │
│  │  /api/signals  /api/alerts  /api/scan  /api/watchlist         │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌───────────────────────▼───────────────────────────────────────┐   │
│  │                   ORCHESTRATOR SERVICE                         │   │
│  │  Coordinates agents, manages scheduling, batches events       │   │
│  └──────┬────────┬────────┬────────┬────────┬────────────────────┘   │
│         │        │        │        │        │                        │
│  ┌──────▼──┐ ┌──▼────┐ ┌─▼─────┐ ┌▼──────┐ ┌▼────────┐            │
│  │Corporate│ │Bulk/  │ │Insider│ │Qtrly  │ │Regulatory│            │
│  │Filings  │ │Block  │ │Trades │ │Results│ │Changes   │            │
│  │Agent    │ │Deals  │ │Agent  │ │Agent  │ │Agent     │            │
│  │         │ │Agent  │ │       │ │       │ │          │            │
│  └──┬──────┘ └──┬────┘ └──┬────┘ └──┬────┘ └──┬───────┘            │
│     │           │         │         │          │                     │
│     └───────────┴─────────┴─────────┴──────────┘                     │
│                          │                                           │
│                    MarketEvents                                      │
│                          │                                           │
│  ┌───────────────────────▼───────────────────────────────────────┐   │
│  │              AI SIGNAL DETECTION ENGINE                        │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐  │   │
│  │  │ Event       │  │ Cross-Event  │  │ Confidence Scoring  │  │   │
│  │  │ Analysis    │  │ Correlation  │  │ & Alert Generation  │  │   │
│  │  │ (GPT-4o)   │  │ Engine       │  │                     │  │   │
│  │  └─────────────┘  └──────────────┘  └─────────────────────┘  │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
│                          │                                           │
│  ┌───────────────────────▼───────────────────────────────────────┐   │
│  │                  SQLite DATABASE                               │   │
│  │  signals │ market_events │ alerts │ watchlist                  │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘

EXTERNAL DATA SOURCES
┌──────────┐  ┌──────────┐  ┌──────────┐
│   NSE    │  │   BSE    │  │   SEBI   │
│ (Filings,│  │ (Cross-  │  │(Circulars│
│  Deals,  │  │  ref)    │  │ Regs)    │
│  Results)│  │          │  │          │
└──────────┘  └──────────┘  └──────────┘
```

---

## Agent Roles & Communication

### 1. Data Ingestion Agents (5 Agents)

| Agent | Data Source | What It Monitors | Output |
|-------|-----------|------------------|--------|
| **CorporateFilingsAgent** | NSE Corporate Announcements API | Board meetings, mergers, demergers, stock splits, bonus issues, buybacks | MarketEvent (filing_*) |
| **BulkBlockDealsAgent** | NSE Large Deals API | Bulk deals (>0.5% of equity) and block deals (institutional) | MarketEvent (bulk_deal, block_deal) |
| **InsiderTradesAgent** | NSE PIT/SAST API | Promoter and insider buying/selling patterns | MarketEvent (insider_trade) |
| **QuarterlyResultsAgent** | NSE Financial Results API | Revenue, profit, margin changes quarter-over-quarter | MarketEvent (quarterly_result) |
| **RegulatoryAgent** | SEBI Website | SEBI circulars, regulatory changes affecting markets | MarketEvent (regulatory_change) |

### 2. Signal Detection Engine (AI Brain)

- **Input:** Batch of MarketEvents from all agents
- **Process:** GPT-4o-mini analyzes events individually and cross-references them
- **Cross-Event Correlation:** Multiple events for the same stock strengthen signals (e.g., promoter buying + good quarterly results = very bullish)
- **Output:** Signals with confidence scores, categorization, and plain-English explanations

### 3. Communication Flow

```
Agents → [MarketEvents] → Orchestrator → [Batches] → Signal Engine → [Signals + Alerts] → API → Frontend
```

- Agents operate independently and write to a shared `market_events` table
- The Orchestrator coordinates execution order and batching
- The Signal Engine processes events in batches of 20 (token limit management)
- High-confidence signals (≥0.8) automatically generate Alerts

---

## Error Handling Logic

| Layer | Error Type | Handling |
|-------|-----------|----------|
| **Agent Fetch** | Network timeout / API down | Log warning, skip agent, continue with others |
| **Agent Parse** | Malformed data | Skip individual item, log warning, process rest |
| **Orchestrator** | Agent crash | Catch exception, record error status, continue scan |
| **Signal Engine** | OpenAI API failure | Log error, return empty signals, events preserved for retry |
| **Signal Engine** | Invalid JSON from AI | Catch parse error, skip batch, log for debugging |
| **Database** | Write failure | Rollback transaction, log error |
| **API Layer** | Request validation | FastAPI automatic 422 with details |
| **Frontend** | API unreachable | Show cached data, retry with exponential backoff |

---

## Key Design Decisions

1. **SQLite for MVP:** Zero-config database, easily upgradeable to PostgreSQL for production
2. **Batch AI Processing:** Events processed in groups of 20 to enable cross-referencing while staying within token limits
3. **Confidence Scoring:** Only signals with ≥0.7 confidence are shown; ≥0.8 trigger alerts
4. **Agent Independence:** Each agent can fail without affecting others — graceful degradation
5. **Polling-based Frontend:** 60-second auto-refresh; upgradeable to WebSocket for real-time push
