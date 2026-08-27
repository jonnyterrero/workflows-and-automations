"""IPO Scoop calendar provider for upcoming public IPO events."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx
import xxhash
from bs4 import BeautifulSoup

from packages.data_providers.base import BaseNewsProvider, ProviderConfig, ProviderError

IPOSCOOP_BASE_URL = "https://www.iposcoop.com"
IPOSCOOP_CALENDAR_URL = f"{IPOSCOOP_BASE_URL}/ipo-calendar/"
_DATE_RE = re.compile(r"(?P<date>\d{1,2}/\d{1,2}/\d{4})")


def _content_hash(company: str, symbol: str, expected_to_trade: str) -> str:
    return xxhash.xxh64(f"{company}|{symbol}|{expected_to_trade}".encode()).hexdigest()


def _clean_symbol(value: str) -> str:
    return value.strip().upper().replace(".", "-")


class IPOScoopCalendarProvider(BaseNewsProvider):
    """Public IPO calendar scraper for research use on allowed public pages."""

    def __init__(self) -> None:
        super().__init__(ProviderConfig(
            name="iposcoop_calendar",
            base_url=IPOSCOOP_BASE_URL,
            timeout_seconds=30.0,
            demo_mode=False,
        ))

    async def _fetch_html(self) -> str:
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds, follow_redirects=True) as client:
            try:
                response = await client.get(
                    IPOSCOOP_CALENDAR_URL,
                    headers={"User-Agent": "trading-intelligence-agent/0.1"},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ProviderError(f"IPO Scoop fetch failed: {exc}") from exc
        return response.text

    def _parse_calendar(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", class_="ipolist")
        if table is None:
            raise ProviderError("IPO Scoop calendar table not found")

        now = datetime.now(tz=UTC).isoformat()
        rows: list[dict[str, Any]] = []
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all("td")
            if len(cells) < 10:
                continue

            company_cell = cells[0]
            company = company_cell.get_text(" ", strip=True)
            symbol = _clean_symbol(cells[1].get_text(" ", strip=True))
            lead_managers = cells[2].get_text(" ", strip=True)
            shares_millions = cells[3].get_text(" ", strip=True)
            price_low = cells[4].get_text(" ", strip=True)
            price_high = cells[5].get_text(" ", strip=True)
            est_volume = cells[6].get_text(" ", strip=True)
            expected_to_trade = cells[7].get_text(" ", strip=True)
            scoop_rating = cells[8].get_text(" ", strip=True)
            rating_change = cells[9].get_text(" ", strip=True)
            company_link = company_cell.find("a")
            url = (
                f"{IPOSCOOP_BASE_URL}{company_link['href']}"
                if company_link and company_link.get("href", "").startswith("/")
                else company_link.get("href")
                if company_link and company_link.get("href")
                else IPOSCOOP_CALENDAR_URL
            )

            summary = (
                f"Lead managers: {lead_managers}. Shares (millions): {shares_millions}. "
                f"Price range: {price_low} to {price_high}. Est. volume: {est_volume}. "
                f"Expected to trade: {expected_to_trade}. Scoop rating: {scoop_rating}. "
                f"Rating change: {rating_change}."
            )
            date_match = _DATE_RE.search(expected_to_trade)
            event_date = None
            if date_match:
                try:
                    event_date = datetime.strptime(date_match.group("date"), "%m/%d/%Y").date().isoformat()
                except ValueError:
                    event_date = None

            rows.append({
                "source": "IPOScoop",
                "author": None,
                "title": f"IPO calendar: {company} ({symbol})",
                "url": url,
                "published_at": now,
                "fetched_at": now,
                "summary": summary[:500],
                "content_hash": _content_hash(company, symbol, expected_to_trade),
                "tickers_mentioned": [symbol] if symbol else [],
                "assets_mentioned": [],
                "raw_text": summary,
                "credibility_score": 0.7,
                "ipo_name": company,
                "ipo_symbol": symbol,
                "event_date": event_date,
                "exchange": None,
                "lead_managers": lead_managers,
                "shares_millions": shares_millions,
                "price_low": price_low,
                "price_high": price_high,
                "est_volume": est_volume,
                "expected_to_trade": expected_to_trade,
                "scoop_rating": scoop_rating,
                "rating_change": rating_change,
            })
        return rows

    async def fetch_ipo_calendar(self, limit: int = 25) -> list[dict[str, Any]]:
        html = await self._fetch_html()
        rows = self._parse_calendar(html)
        items: list[dict[str, Any]] = []
        for row in rows[:limit]:
            items.append({
                "date": row.get("event_date"),
                "name": row.get("ipo_name"),
                "symbol": row.get("ipo_symbol"),
                "exchange": row.get("exchange"),
                "lead_managers": row.get("lead_managers"),
                "shares_millions": row.get("shares_millions"),
                "price_low": row.get("price_low"),
                "price_high": row.get("price_high"),
                "est_volume": row.get("est_volume"),
                "status": row.get("expected_to_trade"),
                "rating": row.get("scoop_rating"),
                "rating_change": row.get("rating_change"),
                "url": row.get("url"),
                "source": "iposcoop",
            })
        return items

    async def fetch_articles(
        self,
        query: str = "",
        limit: int = 20,
        hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        del hours_back
        html = await self._fetch_html()
        rows = self._parse_calendar(html)
        q = query.strip().upper()
        if not q:
            return rows[:limit]

        filtered = [
            row for row in rows
            if q in f"{row['title']} {row.get('summary', '')} {row.get('ipo_symbol', '')}".upper()
        ]
        return filtered[:limit]
