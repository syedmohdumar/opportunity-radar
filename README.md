# Opportunity Radar 🎯

**AI-powered market intelligence that turns corporate filings, bulk deals, insider trades, and quarterly results into actionable investment signals for Indian retail investors.**

> Built for the ET Markets Hackathon — Not a summarizer, a **signal finder**.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green) ![React](https://img.shields.io/badge/React-18-blue) ![Groq](https://img.shields.io/badge/Groq-Llama_3.1-orange)

---

## What It Does

Opportunity Radar deploys **6 autonomous agents** that continuously monitor:

| Agent | Source | Signal |
|-------|--------|--------|
| 📄 Corporate Filings | NSE Announcements | Mergers, splits, bonus, buybacks, board meetings |
| 💰 Bulk/Block Deals | NSE Large Deals | Smart money moves, institutional entry/exit |
| 👤 Insider Trades | NSE PIT/SAST | Promoter buying/selling patterns |
| 📊 Quarterly Results | NSE Financials | Revenue surprises, margin shifts |
| ⚖️ Regulatory Changes | SEBI Circulars | Sector-impacting policy changes |
| 🚀 IPO Watch | NSE IPO Data | Upcoming & active IPO pipeline tracking |

The **AI Signal Detection Engine** (powered by Groq Llama 3.1) then:
1. Analyzes each event for investability
2. Cross-references events across sources (promoter buying + good results = strong signal)
3. Scores confidence (0–100%) and categorizes (bullish/bearish/neutral)
4. Generates plain-English explanations and action suggestions
5. Creates priority alerts for high-confidence signals

### Features

- **Live Market Ticker** — Real-time scrolling index data (NIFTY 50, Bank Nifty, etc.)
- **AI Signal Dashboard** — Filterable signal feed with confidence scores & sparkline charts
- **Smart Alerts** — Priority-based alerts for high-confidence signals
- **Deep Analysis** — On-demand AI deep-dive into any stock
- **IPO Analyzer** — AI-powered IPO risk assessment and scoring
- **AI Video Engine** — Auto-generated animated market update videos (5 types: Market Wrap, Race Chart, Sector Rotation, FII/DII Flows, IPO Tracker) with synthesized background music, animated transitions, and colorful gradient backgrounds

---

## Quick Start — Local Setup

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9+ | macOS ships with 3.9; `python3 --version` to check |
| Node.js | 18+ | Download from [nodejs.org](https://nodejs.org/) |
| Groq API Key | Free | Get one at [console.groq.com](https://console.groq.com/) |

### Step 1: Clone the Repository

```bash
git clone https://github.com/syedmohdumar/opportunity-radar.git
cd opportunity-radar
```

### Step 2: Setup Backend

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate          # Windows

# Install Python dependencies
pip install -r backend/requirements.txt
pip install pydantic-settings
```

### Step 3: Configure Environment

```bash
cp .env.example .env
```

Open `.env` and add your **Groq API key**:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Get a free key at [console.groq.com](https://console.groq.com/) — no credit card required.

### Step 4: Start Backend Server

```bash
# Make sure venv is activated
source venv/bin/activate

# Start FastAPI server
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Backend will be running at **http://localhost:8000**
Swagger API docs at **http://localhost:8000/docs**

### Step 5: Setup & Start Frontend

Open a **new terminal**:

```bash
cd opportunity-radar/frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

Frontend will be running at **http://localhost:5173**

### Step 6: Run Your First Scan

Either:
- Click **"Run Scan"** button in the dashboard header, or
- `POST http://localhost:8000/api/scan/full` via API/curl

```bash
# Via curl
curl -X POST http://localhost:8000/api/scan/full
```

This triggers all 6 agents to scrape NSE/SEBI data and generate AI signals. Wait ~30 seconds for results to appear.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `pip install` fails with build errors | Install Xcode CLT: `xcode-select --install` (macOS) |
| `greenlet` build fails | `pip install greenlet` separately, then retry |
| Port 8000 already in use | `lsof -ti:8000 \| xargs kill -9` then restart |
| Frontend can't reach backend | Check backend is running; Vite proxies `/api` to port 8000 |
| `ModuleNotFoundError: pydantic_settings` | Run `pip install pydantic-settings` |
| Groq API rate limit | Wait 60 seconds and retry; free tier has per-minute limits |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/signals/` | Get filtered signals (category, type, symbol, confidence) |
| `GET` | `/api/signals/top` | Top actionable signals by confidence |
| `GET` | `/api/signals/stats` | Signal statistics (24h, 7d) |
| `GET` | `/api/alerts/` | Get alerts (filterable) |
| `POST` | `/api/alerts/{id}/read` | Mark alert as read |
| `POST` | `/api/scan/full` | Trigger full market scan |
| `POST` | `/api/scan/agent/{name}` | Run specific agent |
| `GET` | `/api/scan/deep-analysis/{symbol}` | AI deep analysis for a stock |
| `GET/POST/DELETE` | `/api/watchlist/` | Manage watchlist |
| `GET` | `/api/market/ticker` | Live market index data |
| `GET` | `/api/ipo/` | IPO listings with AI analysis |
| `GET` | `/api/video/market-wrap` | AI-generated market wrap video |
| `GET` | `/api/video/race-chart` | Stock race chart animation data |
| `GET` | `/api/video/sector-rotation` | Sector rotation heatmap data |
| `GET` | `/api/video/fii-dii` | FII/DII flow visualization |
| `GET` | `/api/video/ipo-tracker` | IPO pipeline tracker |

---

## Project Structure

```
opportunity-radar/
├── backend/
│   ├── agents/                       # 6 data ingestion agents
│   │   ├── base_agent.py             # Base agent class
│   │   ├── corporate_filings_agent.py
│   │   ├── bulk_block_deals_agent.py
│   │   ├── insider_trades_agent.py
│   │   ├── quarterly_results_agent.py
│   │   ├── regulatory_agent.py
│   │   └── ipo_agent.py              # IPO pipeline agent
│   ├── models/
│   │   └── models.py                 # SQLAlchemy models
│   ├── routers/
│   │   ├── signals.py                # Signal endpoints
│   │   ├── alerts.py                 # Alert endpoints
│   │   ├── scan.py                   # Scan trigger endpoints
│   │   ├── watchlist.py              # Watchlist endpoints
│   │   ├── market.py                 # Live market data
│   │   ├── ipo.py                    # IPO analysis endpoints
│   │   └── video.py                  # AI Video Engine endpoints
│   ├── services/
│   │   ├── signal_engine.py          # Groq AI signal detection engine
│   │   └── orchestrator.py           # Agent orchestrator
│   ├── config.py                     # Settings & env config
│   ├── database.py                   # Async SQLite setup
│   ├── main.py                       # FastAPI app entry
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SignalCard.jsx         # Signal display cards
│   │   │   ├── StatsPanel.jsx         # Dashboard statistics
│   │   │   ├── AlertsPanel.jsx        # Smart alerts feed
│   │   │   ├── FilterBar.jsx          # Signal filters
│   │   │   ├── DeepAnalysis.jsx       # AI deep analysis panel
│   │   │   ├── IPOAnalyzer.jsx        # IPO analysis tab
│   │   │   ├── MarketTicker.jsx       # Live scrolling ticker
│   │   │   ├── Sparkline.jsx          # Mini sparkline charts
│   │   │   └── VideoEngine.jsx        # AI Video Engine player
│   │   ├── hooks/useApi.js            # API fetch hooks
│   │   ├── utils/api.js              # API base config
│   │   ├── index.css                  # Tickertape-inspired design system
│   │   ├── App.jsx                    # Main app with routing
│   │   └── main.jsx                   # React entry point
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── vite.config.js                # Vite config with API proxy
├── docs/
│   ├── ARCHITECTURE.md
│   └── IMPACT_MODEL.md
├── .env.example                       # Environment template
├── .gitignore
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9+, FastAPI, SQLAlchemy (async), SQLite |
| AI Engine | Groq (Llama 3.1 8B Instant) — signal detection, video narration, IPO analysis |
| Frontend | React 18, Vite 5, Tailwind CSS, Lucide React Icons |
| Design | Tickertape.in-inspired light theme (#0088EA, #F7F8FA, Inter font) |
| Data Sources | NSE APIs, SEBI Website |
| Audio | Web Audio API (synthesized ambient music in Video Engine) |

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture document with diagrams.

**Key components:**
- **6 Data Ingestion Agents** — independent, fault-tolerant scrapers
- **Orchestrator** — coordinates agents, manages batching
- **AI Signal Engine** — Groq-powered cross-event analysis
- **AI Video Engine** — 5 animated market video types with background music
- **SQLite Database** — zero-config, production-upgradeable to PostgreSQL
- **React Dashboard** — Tickertape-styled signal feed with filters, alerts, video player

---

## What Makes This Different

1. **Signal finding, not summarizing** — Detects patterns humans miss by cross-referencing 6 data sources
2. **Multi-agent architecture** — Each data source has a dedicated agent that can operate independently
3. **Cross-event correlation** — Promoter buying + good results + bulk deal = high-confidence signal
4. **Confidence scoring** — Every signal is scored; only actionable signals surface
5. **AI Video Engine** — Auto-generate animated market update videos with zero editing
6. **IPO Intelligence** — AI-powered red flag detection and scoring for upcoming IPOs
7. **Plain English** — No jargon. Every signal includes a clear explanation and action suggestion

---

## License

MIT
