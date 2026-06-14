"""Provider factory — selects live vs demo providers based on environment."""
from __future__ import annotations

import os
from typing import Any

import structlog

from packages.data_providers.base import (
    BaseCryptoProvider,
    BaseFilingsProvider,
    BaseMacroProvider,
    BaseMarketDataProvider,
    BaseNewsProvider,
    BaseSocialProvider,
    ProviderRegistry,
)
from packages.data_providers.demo.crypto import DemoCryptoProvider
from packages.data_providers.demo.macro import DemoMacroProvider
from packages.data_providers.demo.market import DemoMarketDataProvider
from packages.data_providers.demo.news import DemoNewsProvider
from packages.data_providers.demo.social import DemoSocialProvider
from packages.data_providers.live.alpha_vantage import AlphaVantageMarketProvider
from packages.data_providers.live.alpha_vantage_crypto import AlphaVantageCryptoProvider
from packages.data_providers.live.crypto_rss_news import CryptoRssNewsProvider
from packages.data_providers.live.crypto_feeds_catalog import catalog_summary, load_crypto_rss_catalog
from packages.data_providers.live.fred import FredMacroProvider
from packages.data_providers.live.newsapi import NewsApiProvider
from packages.data_providers.live.reddit_social import RedditSocialProvider
from packages.data_providers.live.rss_news import RssNewsProvider
from packages.data_providers.live.x_setup import get_x_config
from packages.data_providers.live.x_social import XSocialProvider
from packages.filings.edgar import EDGARFilingsProvider

logger = structlog.get_logger()


def is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def _has_key(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def get_market_provider() -> BaseMarketDataProvider:
    if not is_demo_mode() and _has_key("ALPHA_VANTAGE_API_KEY"):
        try:
            return AlphaVantageMarketProvider()
        except Exception as exc:  # noqa: BLE001
            logger.warning("market_provider_fallback", error=str(exc))
    return DemoMarketDataProvider()


def get_macro_provider() -> BaseMacroProvider:
    if not is_demo_mode() and _has_key("FRED_API_KEY"):
        try:
            return FredMacroProvider()
        except Exception as exc:  # noqa: BLE001
            logger.warning("macro_provider_fallback", error=str(exc))
    return DemoMacroProvider()


def get_crypto_provider() -> BaseCryptoProvider:
    if not is_demo_mode() and _has_key("ALPHA_VANTAGE_API_KEY"):
        try:
            return AlphaVantageCryptoProvider()
        except Exception as exc:  # noqa: BLE001
            logger.warning("crypto_provider_fallback", error=str(exc))
    return DemoCryptoProvider()


def get_news_providers() -> list[BaseNewsProvider]:
    if is_demo_mode():
        return [DemoNewsProvider()]

    providers: list[BaseNewsProvider] = [
        RssNewsProvider(),       # equities/macro: Reuters, Bloomberg Markets, Yahoo, etc.
        CryptoRssNewsProvider(),  # crypto: CoinDesk, Bloomberg Crypto, etc.
    ]
    if _has_key("NEWSAPI_KEY"):
        try:
            providers.append(NewsApiProvider())
        except Exception as exc:  # noqa: BLE001
            logger.warning("newsapi_provider_skip", error=str(exc))
    return providers


def get_social_providers() -> list[BaseSocialProvider]:
    if is_demo_mode():
        return [DemoSocialProvider()]
    return [RedditSocialProvider(), XSocialProvider()]


def get_filings_provider() -> BaseFilingsProvider:
    return EDGARFilingsProvider()


def build_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(get_market_provider())
    for news in get_news_providers():
        registry.register(news)
    for social in get_social_providers():
        registry.register(social)
    registry.register(get_macro_provider())
    registry.register(get_crypto_provider())
    registry.register(get_filings_provider())
    return registry


def provider_status() -> dict[str, Any]:
    """Return which providers are active and why."""
    demo = is_demo_mode()
    news: list[str] = ["demo_news"] if demo else ["rss_news", "crypto_rss_news"]
    if not demo and _has_key("NEWSAPI_KEY"):
        news.append("newsapi")

    x_cfg = get_x_config()
    social: list[str] = ["demo_social"] if demo else ["reddit"]
    if not demo and x_cfg["configured"]:
        social.append("x_twitter")

    return {
        "demo_mode": demo,
        "market": "alpha_vantage" if (not demo and _has_key("ALPHA_VANTAGE_API_KEY")) else "demo_market",
        "macro": "fred" if (not demo and _has_key("FRED_API_KEY")) else "demo_macro",
        "crypto": (
            "alpha_vantage_crypto"
            if (not demo and _has_key("ALPHA_VANTAGE_API_KEY"))
            else "demo_crypto"
        ),
        "news": news,
        "social": social,
        "x_api": x_cfg,
        "filings": "edgar",
        "crypto_source_catalog": catalog_summary() if not demo else None,
    }
