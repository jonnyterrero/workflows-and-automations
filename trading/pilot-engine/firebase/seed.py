"""Seed the Firestore source register with known disclosure providers."""

from __future__ import annotations

from typing import Any

from lib.firestore_client import FirestoreClient, get_firestore_client

SOURCES: dict[str, dict[str, Any]] = {
    "capitol_trades": {
        "name": "Capitol Trades",
        "url": "https://www.capitoltrades.com/",
        "type": "scraper",
        "reliability": "B",
        "last_ok": None,
        "notes": "Primary congressional-trade source; ingestion begins in Phase 1.",
    },
    "edgar": {
        "name": "SEC EDGAR",
        "url": "https://www.sec.gov/edgar",
        "type": "filing",
        "reliability": "A",
        "last_ok": None,
        "notes": "Primary 13F filing source for later pilot types.",
    },
    "quiver": {
        "name": "Quiver Quantitative",
        "url": "https://www.quiverquant.com/",
        "type": "api",
        "reliability": "B",
        "last_ok": None,
        "notes": "Optional paid fallback.",
    },
    "apify": {
        "name": "Apify Capitol Trades Scraper",
        "url": "https://apify.com/",
        "type": "scraper",
        "reliability": "B",
        "last_ok": None,
        "notes": "Optional managed-scraper fallback.",
    },
}


def seed_sources(*, client: FirestoreClient | None = None) -> int:
    """Idempotently upsert all declared source-register documents."""
    database = client or get_firestore_client()
    collection = database.collection("source_register")
    for source_id, source in SOURCES.items():
        collection.document(source_id).set(source.copy(), merge=True)
    return len(SOURCES)


def main() -> int:
    """Seed the configured Firestore project."""
    count = seed_sources()
    print(f"Seeded {count} source_register documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
