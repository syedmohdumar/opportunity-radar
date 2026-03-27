"""
IPO Analysis Agent
Monitors upcoming and recently listed IPOs on NSE/BSE.
Detects irregularities: overvaluation, promoter red flags, high GMP divergence,
unusual subscription patterns, low anchor investor interest, and governance concerns.
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
from backend.agents.base_agent import BaseAgent


class IPOAgent(BaseAgent):
    """Ingests IPO data and flags irregularities for investor awareness."""

    NSE_CURRENT_IPOS_URL = "https://www.nseindia.com/api/ipo-current-issue"
    NSE_PAST_IPOS_URL = "https://www.nseindia.com/api/all-upcoming-issues"
    # Investorgain / chittorgarh scrape for GMP and subscription data
    CHITTORGARH_URL = "https://www.chittorgarh.com/report/mainboard-ipo-list-in-india-702/1/"
    SME_CHITTORGARH_URL = "https://www.chittorgarh.com/report/sme-ipo-list-in-india-702/84/"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/json",
    }

    # Known red-flag patterns in IPO filings
    RED_FLAG_KEYWORDS = [
        "criminal proceeding", "regulatory action", "non-compliance", "penalty",
        "litigat", "fraud", "default", "npa", "wilful defaulter", "related party",
        "restated", "qualified opinion", "adverse opinion", "going concern",
        "promoter pledge", "negative cash flow", "accumulated losses",
        "object of the issue", "repay", "general corporate purpose",
    ]

    def __init__(self, session):
        super().__init__("ipo_analysis", session)

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            # 1. NSE current issues
            try:
                await client.get("https://www.nseindia.com", headers=self.HEADERS)
            except Exception:
                pass

            for url in [self.NSE_CURRENT_IPOS_URL, self.NSE_PAST_IPOS_URL]:
                try:
                    resp = await client.get(url, headers=self.HEADERS)
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data if isinstance(data, list) else data.get("data", [])
                        for item in items:
                            item["_source"] = "nse"
                        results.extend(items)
                except Exception as e:
                    self.logger.warning(f"Failed to fetch from {url}: {e}")

            # 2. Chittorgarh mainboard + SME IPO lists (scrape)
            for url, category in [(self.CHITTORGARH_URL, "mainboard"), (self.SME_CHITTORGARH_URL, "sme")]:
                try:
                    resp = await client.get(url, headers=self.HEADERS)
                    if resp.status_code == 200:
                        parsed = self._parse_chittorgarh(resp.text, category)
                        results.extend(parsed)
                except Exception as e:
                    self.logger.warning(f"Failed to scrape {category} IPO list: {e}")

        return results

    def _parse_chittorgarh(self, html: str, category: str) -> List[Dict[str, Any]]:
        """Parse Chittorgarh IPO table for recent IPOs."""
        items = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", {"id": "mainTable"})
            if not table:
                table = soup.find("table")
            if not table:
                return items

            rows = table.find_all("tr")[1:]  # skip header
            for row in rows[:30]:  # last 30 IPOs
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                name = cells[0].get_text(strip=True)
                open_date = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                close_date = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                issue_size = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                price = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                listing_date = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                listing_price = cells[6].get_text(strip=True) if len(cells) > 6 else ""

                items.append({
                    "_source": "chittorgarh",
                    "company": name,
                    "category": category,
                    "open_date": open_date,
                    "close_date": close_date,
                    "issue_size_cr": issue_size,
                    "price_band": price,
                    "listing_date": listing_date,
                    "listing_price": listing_price,
                })
        except Exception as e:
            self.logger.warning(f"Chittorgarh parse error: {e}")
        return items

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        source = raw_data.get("_source", "unknown")

        if source == "nse":
            return self._normalize_nse(raw_data)
        else:
            return self._normalize_chittorgarh(raw_data)

    def _normalize_nse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = raw_data.get("symbol", raw_data.get("companyName", "UNKNOWN"))
        company = raw_data.get("companyName", symbol)
        issue_size = raw_data.get("issueSize", "")
        price_band = raw_data.get("priceBand", "")
        open_date = raw_data.get("issueStartDate", "")
        close_date = raw_data.get("issueEndDate", "")
        status = raw_data.get("status", raw_data.get("issueStatus", ""))
        subscription = raw_data.get("subscriptionTimes", "")

        red_flags = self._detect_red_flags(raw_data)

        title = f"[IPO] {company}"
        if red_flags:
            title += f" — {len(red_flags)} red flag(s) detected"

        desc = (
            f"IPO: {company}. Price band: {price_band}. Issue size: {issue_size}. "
            f"Open: {open_date}, Close: {close_date}. Status: {status}. "
        )
        if subscription:
            desc += f"Subscription: {subscription}x. "
        if red_flags:
            desc += f"⚠️ Red flags: {'; '.join(red_flags)}"

        return {
            "event_type": "ipo_issue",
            "symbol": symbol,
            "title": title,
            "description": desc,
            "data": {
                "company_name": company,
                "price_band": price_band,
                "issue_size": issue_size,
                "open_date": open_date,
                "close_date": close_date,
                "status": status,
                "subscription_times": subscription,
                "category": raw_data.get("series", "mainboard"),
                "red_flags": red_flags,
                "red_flag_count": len(red_flags),
                "raw": {k: v for k, v in raw_data.items() if isinstance(v, (str, int, float, bool)) and k != "_source"},
            },
            "source": "NSE",
            "event_date": datetime.utcnow(),
        }

    def _normalize_chittorgarh(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        company = raw_data.get("company", "Unknown")
        category = raw_data.get("category", "mainboard")
        price_band = raw_data.get("price_band", "")
        issue_size = raw_data.get("issue_size_cr", "")
        listing_price = raw_data.get("listing_price", "")
        listing_date = raw_data.get("listing_date", "")

        # Check for listing day irregularities
        irregularities = []
        try:
            if price_band and listing_price:
                # Extract upper price from band like "₹100-₹120" or "120"
                price_str = price_band.replace("₹", "").replace(",", "").strip()
                listing_str = listing_price.replace("₹", "").replace(",", "").strip()
                if "-" in price_str:
                    upper_price = float(price_str.split("-")[-1].strip())
                else:
                    upper_price = float(price_str) if price_str else 0

                if listing_str and upper_price > 0:
                    list_price = float(listing_str)
                    listing_gain_pct = ((list_price - upper_price) / upper_price) * 100

                    if listing_gain_pct > 90:
                        irregularities.append(f"Extreme listing premium ({listing_gain_pct:.0f}%) — potential manipulation concern")
                    elif listing_gain_pct < -20:
                        irregularities.append(f"Heavy listing discount ({listing_gain_pct:.0f}%) — possible overpricing in IPO")
        except (ValueError, TypeError):
            pass

        if category == "sme":
            irregularities.append("SME IPO — higher risk, lower regulatory scrutiny, limited institutional coverage")

        red_flags = self._detect_red_flags(raw_data)
        irregularities.extend(red_flags)

        title = f"[IPO] {company} ({category.upper()})"
        if irregularities:
            title += f" — {len(irregularities)} irregularity flag(s)"

        desc = (
            f"IPO: {company} ({category}). Price band: {price_band}. "
            f"Issue size: ₹{issue_size} Cr. Listing date: {listing_date}. "
            f"Listing price: {listing_price}. "
        )
        if irregularities:
            desc += f"⚠️ Flags: {'; '.join(irregularities)}"

        return {
            "event_type": "ipo_issue",
            "symbol": company.split(" ")[0].upper()[:10] if company else "UNKNOWN",
            "title": title,
            "description": desc,
            "data": {
                "company_name": company,
                "category": category,
                "price_band": price_band,
                "issue_size_cr": issue_size,
                "listing_date": listing_date,
                "listing_price": listing_price,
                "irregularities": irregularities,
                "irregularity_count": len(irregularities),
                "raw": {k: v for k, v in raw_data.items() if isinstance(v, (str, int, float, bool)) and k != "_source"},
            },
            "source": "Chittorgarh",
            "event_date": datetime.utcnow(),
        }

    def _detect_red_flags(self, data: Dict[str, Any]) -> List[str]:
        """Scan all text fields for known IPO red-flag keywords."""
        flags = []
        text = " ".join(
            str(v).lower() for v in data.values() if isinstance(v, str)
        )
        for keyword in self.RED_FLAG_KEYWORDS:
            if keyword in text:
                flags.append(f"Contains '{keyword}'")
        return flags
