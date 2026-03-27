"""
Quarterly Results Agent
Monitors quarterly financial results — revenue growth, profit surprises,
margin expansion/contraction, and management guidance.
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any
from backend.agents.base_agent import BaseAgent


class QuarterlyResultsAgent(BaseAgent):
    """Ingests quarterly financial results data."""

    NSE_RESULTS_URL = "https://www.nseindia.com/api/corporate-financial-results"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    def __init__(self, session):
        super().__init__("quarterly_results", session)

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                await client.get("https://www.nseindia.com", headers=self.HEADERS)
            except Exception:
                pass

            try:
                params = {"index": "equities", "period": "Quarterly"}
                resp = await client.get(self.NSE_RESULTS_URL, params=params, headers=self.HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("data", [])
                    results.extend(items)
            except Exception as e:
                self.logger.warning(f"Failed to fetch quarterly results: {e}")

        return results

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = raw_data.get("symbol", "UNKNOWN")
        company = raw_data.get("companyName", symbol)
        revenue = self._parse_number(raw_data.get("revenueFromOperations", raw_data.get("income", 0)))
        net_profit = self._parse_number(raw_data.get("netProfit", raw_data.get("pAfterTax", 0)))
        period = raw_data.get("period", raw_data.get("quarterEnded", ""))

        # Revenue and profit growth signals
        prev_revenue = self._parse_number(raw_data.get("prevRevenue", 0))
        prev_profit = self._parse_number(raw_data.get("prevNetProfit", 0))

        revenue_growth = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else None
        profit_growth = ((net_profit - prev_profit) / prev_profit * 100) if prev_profit > 0 else None

        growth_desc_parts = []
        if revenue_growth is not None:
            growth_desc_parts.append(f"Revenue growth: {revenue_growth:+.1f}%")
        if profit_growth is not None:
            growth_desc_parts.append(f"Profit growth: {profit_growth:+.1f}%")
        growth_desc = ". ".join(growth_desc_parts) if growth_desc_parts else "Growth data pending comparison."

        return {
            "event_type": "quarterly_result",
            "symbol": symbol,
            "title": f"[{symbol}] Quarterly Results — {period}",
            "description": f"{company} reported quarterly results for {period}. "
                          f"Revenue: ₹{revenue:,.0f} Cr, Net Profit: ₹{net_profit:,.0f} Cr. {growth_desc}",
            "data": {
                "company_name": company,
                "period": period,
                "revenue": revenue,
                "net_profit": net_profit,
                "revenue_growth_pct": revenue_growth,
                "profit_growth_pct": profit_growth,
                "raw": {k: v for k, v in raw_data.items() if isinstance(v, (str, int, float, bool))},
            },
            "source": "NSE",
            "event_date": datetime.utcnow(),
        }

    @staticmethod
    def _parse_number(val) -> float:
        if val is None:
            return 0.0
        try:
            return float(str(val).replace(",", "").replace("-", "0") or "0")
        except (ValueError, TypeError):
            return 0.0
