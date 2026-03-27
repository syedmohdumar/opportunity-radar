"""
Bulk & Block Deals Agent
Monitors bulk deals and block deals on NSE — large quantity trades
that often signal institutional interest or exit.
"""
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.agents.base_agent import BaseAgent


class BulkBlockDealsAgent(BaseAgent):
    """Ingests bulk and block deal data from NSE."""

    NSE_BULK_DEALS_URL = "https://www.nseindia.com/api/snapshot-capital-market-large-deals"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    def __init__(self, session):
        super().__init__("bulk_block_deals", session)

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                await client.get("https://www.nseindia.com", headers=self.HEADERS)
            except Exception:
                pass

            try:
                resp = await client.get(self.NSE_BULK_DEALS_URL, headers=self.HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    # NSE returns {BLOCK_DEALS: [...], BULK_DEALS: [...]}
                    for deal_type in ["BLOCK_DEALS", "BULK_DEALS"]:
                        for deal in data.get(deal_type, []):
                            deal["_deal_type"] = deal_type.lower().replace("_deals", "")
                            results.append(deal)
            except Exception as e:
                self.logger.warning(f"Failed to fetch bulk/block deals: {e}")

        return results

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        deal_type = raw_data.get("_deal_type", "bulk")
        symbol = raw_data.get("symbol", raw_data.get("SYMBOL", "UNKNOWN"))
        client_name = raw_data.get("clientName", raw_data.get("CLIENT_NAME", "Unknown"))
        trade_type = raw_data.get("buySell", raw_data.get("BUY_SELL", ""))
        quantity = raw_data.get("quantity", raw_data.get("QUANTITY", 0))
        price = raw_data.get("tradePrice", raw_data.get("TRADE_PRICE", 0))

        try:
            quantity = int(str(quantity).replace(",", ""))
        except (ValueError, TypeError):
            quantity = 0
        try:
            price = float(str(price).replace(",", ""))
        except (ValueError, TypeError):
            price = 0.0

        trade_value = quantity * price
        action = "bought" if trade_type.upper() in ["BUY", "B"] else "sold"

        return {
            "event_type": f"{deal_type}_deal",
            "symbol": symbol,
            "title": f"[{symbol}] {client_name} {action} {quantity:,} shares @ ₹{price:,.2f} ({deal_type} deal)",
            "description": f"{client_name} {action} {quantity:,} shares of {symbol} at ₹{price:,.2f} per share. "
                          f"Total trade value: ₹{trade_value:,.0f}. Deal type: {deal_type}.",
            "data": {
                "deal_type": deal_type,
                "client_name": client_name,
                "trade_type": trade_type,
                "quantity": quantity,
                "price": price,
                "trade_value": trade_value,
                "raw": {k: v for k, v in raw_data.items() if k != "_deal_type" and isinstance(v, (str, int, float, bool))},
            },
            "source": "NSE",
            "event_date": datetime.utcnow(),
        }
