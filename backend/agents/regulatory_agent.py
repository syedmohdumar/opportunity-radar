"""
Regulatory Changes Agent
Monitors SEBI circulars and regulatory changes that can impact market sectors.
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.agents.base_agent import BaseAgent


class RegulatoryAgent(BaseAgent):
    """Ingests SEBI circulars and regulatory updates."""

    SEBI_CIRCULARS_URL = "https://www.sebi.gov.in/sebiweb/ajax/getLatestCirculars.jsp"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/json",
    }

    def __init__(self, session):
        super().__init__("regulatory", session)

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get("https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=1&smid=0", headers=self.HEADERS)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    rows = soup.select("table tr")
                    for row in rows[1:21]:  # Last 20 circulars
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            link = cols[1].find("a")
                            results.append({
                                "date": cols[0].get_text(strip=True),
                                "title": cols[1].get_text(strip=True),
                                "url": f"https://www.sebi.gov.in{link['href']}" if link and link.get("href") else "",
                                "category": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                            })
            except Exception as e:
                self.logger.warning(f"Failed to fetch SEBI circulars: {e}")

        return results

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        title = raw_data.get("title", "Regulatory Update")
        category = raw_data.get("category", "")

        # Classify impact sectors
        sector_keywords = {
            "banking": ["bank", "nbd", "lending", "deposit", "rbi"],
            "mutual_fund": ["mutual fund", "amc", "scheme", "sip"],
            "insurance": ["insurance", "irdai"],
            "markets": ["trading", "margin", "settlement", "listing", "ipo", "sme"],
            "corporate": ["governance", "board", "disclosure", "related party"],
        }

        affected_sectors = []
        text_lower = (title + " " + category).lower()
        for sector, keywords in sector_keywords.items():
            if any(kw in text_lower for kw in keywords):
                affected_sectors.append(sector)

        return {
            "event_type": "regulatory_change",
            "symbol": None,
            "title": f"[SEBI] {title[:200]}",
            "description": f"SEBI circular: {title}. Category: {category}. "
                          f"Potentially affected sectors: {', '.join(affected_sectors) if affected_sectors else 'Broad market'}.",
            "data": {
                "category": category,
                "affected_sectors": affected_sectors,
                "url": raw_data.get("url", ""),
                "date_str": raw_data.get("date", ""),
            },
            "source": "SEBI",
            "event_date": datetime.utcnow(),
        }
