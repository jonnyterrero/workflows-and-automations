from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssetClass(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    BOND_ETF = "bond_etf"
    CRYPTO = "crypto"
    INDEX = "index"
    COMMODITY = "commodity"
    FOREX = "forex"


class SignalDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class SignalHorizon(str, Enum):
    INTRADAY = "intraday"
    SWING = "swing"
    LONG_TERM = "long_term"


class SignalType(str, Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    SENTIMENT = "sentiment"
    EVENT = "event"
    RISK = "risk"
    COMPOSITE = "composite"


class ParseStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ThesisStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Asset(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    symbol: str
    name: str
    asset_class: AssetClass
    exchange: str | None = None
    currency: str = "USD"
    sector: str | None = None
    industry: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AssetCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    asset_class: AssetClass
    exchange: str | None = None
    currency: str = "USD"
    sector: str | None = None
    industry: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class WatchlistEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    symbol: str = ""
    notes: str | None = None
    added_at: datetime | None = None


class MarketPrice(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    timestamp: datetime
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float
    volume: float | None = None
    source: str
    interval: str = "1d"
    raw_payload_id: int | None = None


class TradeEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    timestamp: datetime
    price: float
    size: float
    side: str
    exchange: str
    source: str
    raw_payload_id: int | None = None


class OrderBookSnapshot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    timestamp: datetime
    bids: list[list[float]] = Field(default_factory=list)
    asks: list[list[float]] = Field(default_factory=list)
    exchange: str
    source: str
    raw_payload_id: int | None = None


class OrderBookDelta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    timestamp: datetime
    side: str
    price: float
    size: float
    sequence: int
    exchange: str
    source: str
    raw_payload_id: int | None = None


class NewsArticle(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    source: str
    author: str | None = None
    title: str
    url: str
    published_at: datetime
    fetched_at: datetime
    summary: str | None = None
    content_hash: str
    tickers_mentioned: list[str] = Field(default_factory=list)
    assets_mentioned: list[str] = Field(default_factory=list)
    raw_text: str | None = None
    credibility_score: float = 0.5
    raw_payload_id: int | None = None


class SocialPost(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    platform: str
    source_community: str | None = None
    author_hash: str
    url: str | None = None
    posted_at: datetime
    fetched_at: datetime
    text: str
    tickers_mentioned: list[str] = Field(default_factory=list)
    assets_mentioned: list[str] = Field(default_factory=list)
    engagement_score: float = 0.0
    credibility_score: float = 0.5
    sentiment_score: float = 0.0
    toxicity_or_spam_score: float = 0.0
    raw_payload_id: int | None = None


class MacroIndicator(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str
    timestamp: datetime
    value: float
    unit: str
    source: str
    category: str
    raw_payload_id: int | None = None


class FilingDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    company_symbol: str
    filing_type: str
    filed_at: datetime
    url: str
    accession_number: str
    text: str | None = None
    summary: str | None = None
    risk_items: list[str] = Field(default_factory=list)
    raw_payload_id: int | None = None


class Signal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    timestamp: datetime
    horizon: SignalHorizon
    signal_type: SignalType
    direction: SignalDirection
    score: float = Field(ge=-100.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[int] = Field(default_factory=list)
    reasoning: str
    counterarguments: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    created_by: str = "system"
    version: str = "1.0"


class TradeThesis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    timestamp: datetime
    title: str
    thesis_summary: str
    direction: SignalDirection
    time_horizon: SignalHorizon
    entry_zone: str | None = None
    invalidation_level: str | None = None
    risk_reward_notes: str | None = None
    evidence_ids: list[int] = Field(default_factory=list)
    counterarguments: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    disclaimer: str
    status: ThesisStatus = ThesisStatus.DRAFT


class RawPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    source: str
    provider: str
    endpoint: str
    fetched_at: datetime
    payload_hash: str
    payload_json: dict[str, Any] | None = None
    payload_text: str | None = None
    parse_status: ParseStatus = ParseStatus.PENDING
    error_message: str | None = None


class DailyBriefing(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    date: date
    market_regime_summary: str
    macro_summary: str
    equity_summary: str
    etf_summary: str
    bond_summary: str
    crypto_summary: str
    top_opportunities: list[dict[str, Any]] = Field(default_factory=list)
    top_risks: list[dict[str, Any]] = Field(default_factory=list)
    unusual_social_activity: list[dict[str, Any]] = Field(default_factory=list)
    major_news_events: list[dict[str, Any]] = Field(default_factory=list)
    watchlist_changes: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ids: list[int] = Field(default_factory=list)
    disclaimer: str
    created_at: datetime | None = None


class AssetResearchReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    asset_id: int
    date: date
    current_context: str
    bullish_case: str
    bearish_case: str
    technical_context: str
    fundamental_context: str
    macro_context: str
    sentiment_context: str
    risk_flags: list[str] = Field(default_factory=list)
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[int] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)
    disclaimer: str
    created_at: datetime | None = None


class SignalExplanation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    signal_id: int | None = None
    asset_symbol: str
    signal_direction: SignalDirection
    signal_score: float
    confidence: float
    strongest_evidence: list[dict[str, Any]] = Field(default_factory=list)
    contradicting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    what_would_invalidate: str
    risk_notes: str
    evidence_ids: list[int] = Field(default_factory=list)
    disclaimer: str


class ProviderHealthStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider_name: str
    is_healthy: bool
    last_check: datetime
    error_message: str | None = None
    requests_today: int = 0
    rate_limit_remaining: int | None = None
