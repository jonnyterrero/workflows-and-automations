"""Unit tests for provider factory."""
from __future__ import annotations

import pytest

from packages.data_providers.demo.macro import DemoMacroProvider
from packages.data_providers.demo.market import DemoMarketDataProvider
from packages.data_providers.factory import (
    get_macro_provider,
    get_market_provider,
    get_news_providers,
    provider_status,
)
from packages.data_providers.live.alpha_vantage import AlphaVantageMarketProvider
from packages.data_providers.live.alpha_vantage_crypto import AlphaVantageCryptoProvider
from packages.data_providers.live.coinbase_exchange import CoinbaseExchangeCryptoProvider
from packages.data_providers.live.finnhub_fundamentals import FinnhubFundamentalsProvider
from packages.data_providers.live.fred import FredMacroProvider
from packages.data_providers.live.iposcoop_calendar import IPOScoopCalendarProvider
from packages.data_providers.live.polygon_market import PolygonMarketProvider
from packages.data_providers.live.rss_news import RssNewsProvider
from packages.data_providers.live.sec_api_filings import SecApiFilingsProvider


def test_demo_mode_uses_demo_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

    assert isinstance(get_market_provider(), DemoMarketDataProvider)
    assert isinstance(get_macro_provider(), DemoMacroProvider)
    assert len(get_news_providers()) == 1
    assert get_news_providers()[0].config.name == "demo_news"


def test_live_mode_uses_real_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("FRED_API_KEY", "test-fred")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-av")
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)

    assert isinstance(get_market_provider(), AlphaVantageMarketProvider)
    assert isinstance(get_macro_provider(), FredMacroProvider)
    news = get_news_providers()
    assert any(p.config.name == "rss_news" for p in news)
    assert any(p.config.name == "crypto_rss_news" for p in news)
    assert any(p.config.name == "iposcoop_calendar" for p in news)


def test_live_crypto_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-av")
    monkeypatch.setenv("COINBASE_USE_PUBLIC_MARKET_DATA", "false")
    from packages.data_providers.factory import get_crypto_provider
    assert isinstance(get_crypto_provider(), AlphaVantageCryptoProvider)


def test_provider_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("FRED_API_KEY", "k")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    status = provider_status()
    assert status["demo_mode"] is False
    assert status["market"] == "alpha_vantage"
    assert status["macro"] == "fred"
    assert status["crypto"] == "coinbase_exchange"
    assert "rss_news" in status["news"]
    assert "crypto_rss_news" in status["news"]
    assert "iposcoop_calendar" in status["news"]


def test_default_rss_feeds_drop_dead_reuters_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RSS_FEED_URLS", raising=False)
    provider = RssNewsProvider()
    urls = [url for _, url in provider._feeds]
    assert all("reuters.com" not in url for url in urls)
    assert any("investing.com/rss/news_25.rss" in url for url in urls)


def test_polygon_preferred_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("POLYGON_API_KEY", "poly")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "av")
    assert isinstance(get_market_provider(), PolygonMarketProvider)


def test_coinbase_public_crypto_provider_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.setenv("COINBASE_USE_PUBLIC_MARKET_DATA", "true")
    from packages.data_providers.factory import get_crypto_provider
    assert isinstance(get_crypto_provider(), CoinbaseExchangeCryptoProvider)


def test_finnhub_and_sec_api_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("FINNHUB_API_KEY", "fh")
    monkeypatch.setenv("SEC_API_KEY", "sec")
    from packages.data_providers.factory import get_filings_provider, get_fundamentals_provider
    assert any(p.config.name == "finnhub_news" for p in get_news_providers())
    assert isinstance(get_fundamentals_provider(), FinnhubFundamentalsProvider)
    assert isinstance(get_filings_provider(), SecApiFilingsProvider)


def test_iposcoop_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("ENABLE_IPOSCOOP_SCRAPER", "false")
    news = get_news_providers()
    assert not any(isinstance(provider, IPOScoopCalendarProvider) for provider in news)
