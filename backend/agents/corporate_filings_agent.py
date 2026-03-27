"""
Corporate Filings Agent
Monitors NSE/BSE corporate filings (board meetings, AGMs, corporate actions,
scheme of arrangements, mergers, demergers, stock splits, bonus issues).
"""
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.agents.base_agent import BaseAgent


class CorporateFilingsAgent(BaseAgent):
    """Ingests corporate filing data from NSE."""

    NSE_CORPORATE_FILINGS_URL = "https://www.nseindia.com/api/corporate-announcements"
    NSE_BOARD_MEETINGS_URL = "https://www.nseindia.com/api/corporate-board-meetings"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, session):
        super().__init__("corporate_filings", session)

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            # First hit the main page to get cookies
            try:
                await client.get("https://www.nseindia.com", headers=self.HEADERS)
            except Exception:
                pass

            # Fetch corporate announcements
            try:
                params = {"index": "equities", "from_date": (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y"), "to_date": datetime.now().strftime("%d-%m-%Y")}
                resp = await client.get(self.NSE_CORPORATE_FILINGS_URL, params=params, headers=self.HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data if isinstance(data, list) else data.get("data", []):
                        item["_source_type"] = "announcement"
                        results.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to fetch announcements: {e}")

            # Fetch board meetings
            try:
                resp = await client.get(self.NSE_BOARD_MEETINGS_URL, params={"index": "equities"}, headers=self.HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data if isinstance(data, list) else data.get("data", []):
                        item["_source_type"] = "board_meeting"
                        results.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to fetch board meetings: {e}")

        return results

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        source_type = raw_data.get("_source_type", "announcement")
        symbol = raw_data.get("symbol", raw_data.get("sym", "UNKNOWN"))
        company = raw_data.get("company", raw_data.get("companyName", symbol))
        subject = raw_data.get("subject", raw_data.get("purpose", "Corporate Filing"))
        description = raw_data.get("desc", raw_data.get("description", subject))

        # Classify filing type for signal detection
        filing_keywords = {
            "merger": ["merger", "amalgamation", "scheme of arrangement"],
            "bonus": ["bonus"],
            "split": ["split", "sub-division"],
            "buyback": ["buyback", "buy-back"],
            "dividend": ["dividend"],
            "rights_issue": ["rights issue"],
            "board_meeting": ["board meeting", "results"],
            "acquisition": ["acquisition", "acquire"],
        }

        filing_subtype = "general"
        desc_lower = (subject + " " + description).lower()
        for subtype, keywords in filing_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                filing_subtype = subtype
                break

        return {
            "event_type": f"filing_{filing_subtype}",
            "symbol": symbol,
            "title": f"[{symbol}] {subject[:200]}",
            "description": description[:2000],
            "data": {
                "filing_subtype": filing_subtype,
                "source_type": source_type,
                "company_name": company,
                "raw": {k: v for k, v in raw_data.items() if k != "_source_type" and isinstance(v, (str, int, float, bool))},
            },
            "source": "NSE",
            "event_date": datetime.utcnow(),
        }
