"""Abstract base classes and shared infrastructure for all data providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import os
from typing import Any

import structlog

logger = structlog.get_logger()

DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 30
    requests_per_day: int = 500
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0


@dataclass
class ProviderConfig:
    name: str
    api_key: str | None = None
    base_url: str = ""
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    timeout_seconds: float = 30.0
    demo_mode: bool = False


class ProviderError(Exception):
    """Base provider error."""


class RateLimitError(ProviderError):
    """Provider rate limit hit."""


class AuthError(ProviderError):
    """API key missing or invalid."""


class ParseError(ProviderError):
    """Response parse failure."""


class BaseMarketDataProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def fetch_ohlcv(
        self, symbol: str, interval: str, start: datetime, end: datetime,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def fetch_latest_quote(self, symbol: str) -> dict[str, Any] | None: ...

    async def fetch_batch_ohlcv(
        self, symbols: list[str], interval: str, start: datetime, end: datetime,
    ) -> dict[str, list[dict[str, Any]]]:
        results: dict[str, list[dict[str, Any]]] = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.fetch_ohlcv(symbol, interval, start, end)
            except ProviderError as exc:
                logger.warning("batch_ohlcv_failed", provider=self.config.name, symbol=symbol, error=str(exc))
                results[symbol] = []
        return results


class BaseNewsProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def fetch_articles(
        self, query: str, limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]: ...

    async def fetch_for_symbols(
        self, symbols: list[str], limit_per_symbol: int = 10, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        seen: set[str] = set()
        for symbol in symbols:
            try:
                batch = await self.fetch_articles(query=symbol, limit=limit_per_symbol, hours_back=hours_back)
                for a in batch:
                    h = a.get("content_hash", "")
                    if h and h not in seen:
                        seen.add(h)
                        articles.append(a)
            except ProviderError as exc:
                logger.warning("fetch_articles_failed", provider=self.config.name, symbol=symbol, error=str(exc))
        return articles


class BaseSocialProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def fetch_posts(
        self, query: str, subreddit_or_community: str = "",
        limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]: ...

    async def fetch_for_symbols(
        self, symbols: list[str], limit_per_symbol: int = 10, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        posts: list[dict[str, Any]] = []
        for symbol in symbols:
            try:
                posts.extend(await self.fetch_posts(query=symbol, limit=limit_per_symbol, hours_back=hours_back))
            except ProviderError as exc:
                logger.warning("fetch_posts_failed", provider=self.config.name, symbol=symbol, error=str(exc))
        return posts


class BaseMacroProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def fetch_indicator(self, series_id: str, limit: int = 12) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def fetch_yield_curve(self) -> list[dict[str, Any]]: ...


class BaseCryptoProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, interval: str = "1d", limit: int = 60) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def fetch_order_book(self, symbol: str, depth: int = 10) -> dict[str, Any] | None: ...


class BaseFundamentalsProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def fetch_overview(self, symbol: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def fetch_earnings(self, symbol: str) -> list[dict[str, Any]]: ...


class BaseFilingsProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def fetch_recent_filings(
        self, symbol: str, filing_types: list[str], limit: int = 10,
    ) -> list[dict[str, Any]]: ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._market: dict[str, BaseMarketDataProvider] = {}
        self._news: dict[str, BaseNewsProvider] = {}
        self._social: dict[str, BaseSocialProvider] = {}
        self._macro: dict[str, BaseMacroProvider] = {}
        self._crypto: dict[str, BaseCryptoProvider] = {}
        self._fundamentals: dict[str, BaseFundamentalsProvider] = {}
        self._filings: dict[str, BaseFilingsProvider] = {}

    def register(self, provider: Any) -> None:
        name = provider.config.name
        if isinstance(provider, BaseMarketDataProvider):
            self._market[name] = provider
        elif isinstance(provider, BaseNewsProvider):
            self._news[name] = provider
        elif isinstance(provider, BaseSocialProvider):
            self._social[name] = provider
        elif isinstance(provider, BaseMacroProvider):
            self._macro[name] = provider
        elif isinstance(provider, BaseCryptoProvider):
            self._crypto[name] = provider
        elif isinstance(provider, BaseFundamentalsProvider):
            self._fundamentals[name] = provider
        elif isinstance(provider, BaseFilingsProvider):
            self._filings[name] = provider
        else:
            raise TypeError(f"Unknown provider type: {type(provider)}")
        logger.info("provider_registered", name=name, type=type(provider).__name__)

    def get_market_provider(self, name: str) -> BaseMarketDataProvider:
        return self._market[name]

    def get_news_providers(self) -> list[BaseNewsProvider]:
        return list(self._news.values())

    def get_social_providers(self) -> list[BaseSocialProvider]:
        return list(self._social.values())

    def get_macro_providers(self) -> list[BaseMacroProvider]:
        return list(self._macro.values())

    def get_crypto_provider(self, name: str) -> BaseCryptoProvider:
        return self._crypto[name]

    def get_fundamentals_provider(self, name: str) -> BaseFundamentalsProvider:
        return self._fundamentals[name]

    def get_filings_provider(self, name: str) -> BaseFilingsProvider:
        return self._filings[name]
