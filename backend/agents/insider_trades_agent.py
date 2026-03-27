"""
Insider Trades Agent
Monitors SAST (Substantial Acquisition of Shares and Takeovers) and
insider trading data — promoter buying/selling is a strong signal.
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any
from backend.agents.base_agent import BaseAgent


class InsiderTradesAgent(BaseAgent):
    """Ingests insider/promoter trading data from NSE."""

    NSE_INSIDER_URL = "https://www.nseindia.com/api/corporates-pit"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    def __init__(self, session):
        super().__init__("insider_trades", session)

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                await client.get("https://www.nseindia.com", headers=self.HEADERS)
            except Exception:
                pass

            try:
                resp = await client.get(self.NSE_INSIDER_URL, params={"index": "equities"}, headers=self.HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("data", [])
                    results.extend(items)
            except Exception as e:
                self.logger.warning(f"Failed to fetch insider trades: {e}")

        return results

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = raw_data.get("symbol", "UNKNOWN")
        person = raw_data.get("acqName", raw_data.get("personName", "Unknown"))
        category = raw_data.get("categoryOfPerson", raw_data.get("personCategory", ""))
        transaction_type = raw_data.get("tdpTransactionType", raw_data.get("transactionType", ""))
        shares = raw_data.get("secAcq", raw_data.get("noOfShareAcq", 0))
        value = raw_data.get("secVal", raw_data.get("valueOfShareAcq", 0))

        try:
            shares = int(str(shares).replace(",", "").replace("-", "0") or "0")
        except (ValueError, TypeError):
            shares = 0
        try:
            value = float(str(value).replace(",", "").replace("-", "0") or "0")
        except (ValueError, TypeError):
            value = 0.0

        is_promoter = "promoter" in category.lower()
        action = "acquired" if "acquisition" in transaction_type.lower() or "buy" in transaction_type.lower() else "disposed"

        # Promoter buying is a strong bullish signal
        significance = "high" if is_promoter else "medium"

        return {
            "event_type": "insider_trade",
            "symbol": symbol,
            "title": f"[{symbol}] {person} ({category}) {action} {shares:,} shares",
            "description": f"Insider trade: {person} ({category}) {action} {shares:,} shares of {symbol}. "
                          f"Transaction value: ₹{value:,.0f}. "
                          f"{'⚡ Promoter activity detected — high significance.' if is_promoter else ''}",
            "data": {
                "person_name": person,
                "category": category,
                "transaction_type": transaction_type,
                "shares": shares,
                "value": value,
                "is_promoter": is_promoter,
                "action": action,
                "significance": significance,
                "raw": {k: v for k, v in raw_data.items() if isinstance(v, (str, int, float, bool))},
            },
            "source": "NSE",
            "event_date": datetime.utcnow(),
        }
