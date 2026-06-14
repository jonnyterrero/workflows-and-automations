"""Load curated crypto RSS catalog from config/crypto_rss_feeds.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_CATALOG_PATH = Path(__file__).resolve().parents[3] / "config" / "crypto_rss_feeds.yaml"


@dataclass(frozen=True)
class CryptoFeedEntry:
    name: str
    url: str
    category: str
    reliability: int
    monitor: str = "daily"

    @property
    def credibility_score(self) -> float:
        """Map 1-10 reliability to 0.55-0.95 credibility for news scoring."""
        return round(0.45 + (self.reliability / 10) * 0.5, 2)


def load_crypto_rss_catalog(path: Path | None = None) -> list[CryptoFeedEntry]:
    catalog_path = path or _CATALOG_PATH
    if not catalog_path.exists():
        return []

    with catalog_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    entries: list[CryptoFeedEntry] = []
    for category, feeds in (data.get("rss_feeds") or {}).items():
        for feed in feeds or []:
            if not feed.get("url"):
                continue
            entries.append(CryptoFeedEntry(
                name=str(feed.get("name", "Unknown")),
                url=str(feed["url"]),
                category=str(category),
                reliability=int(feed.get("reliability", 7)),
                monitor=str(feed.get("monitor", "daily")),
            ))
    return entries


def load_api_integrations(path: Path | None = None) -> list[dict[str, Any]]:
    catalog_path = path or _CATALOG_PATH
    if not catalog_path.exists():
        return []

    with catalog_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    integrations: list[dict[str, Any]] = []
    for group, items in (data.get("api_integrations") or {}).items():
        for item in items or []:
            integrations.append({**item, "group": group})
    return integrations


def catalog_summary() -> dict[str, Any]:
    feeds = load_crypto_rss_catalog()
    apis = load_api_integrations()
    by_category: dict[str, int] = {}
    for f in feeds:
        by_category[f.category] = by_category.get(f.category, 0) + 1
    return {
        "rss_feed_count": len(feeds),
        "rss_by_category": by_category,
        "rss_sources": [
            {
                "name": f.name,
                "category": f.category,
                "reliability": f.reliability,
                "monitor": f.monitor,
                "url": f.url,
            }
            for f in feeds
        ],
        "api_integrations_pending": len(apis),
        "api_integrations": apis,
    }
