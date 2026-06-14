from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AssetTable(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("symbol", "exchange", name="uq_assets_symbol_exchange"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(30), nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    theme_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class WatchlistTable(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("asset_id", name="uq_watchlist_asset"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MarketPriceTable(Base):
    __tablename__ = "market_prices"
    __table_args__ = (
        UniqueConstraint("asset_id", "timestamp", "interval", "source", name="uq_market_price"),
        Index("ix_market_prices_asset_interval_timestamp", "asset_id", "interval", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open: Mapped[float | None] = mapped_column(Float, nullable=True)
    high: Mapped[float | None] = mapped_column(Float, nullable=True)
    low: Mapped[float | None] = mapped_column(Float, nullable=True)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    interval: Mapped[str] = mapped_column(String(10), nullable=False, default="1d")
    raw_payload_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RawPayloadTable(Base):
    __tablename__ = "raw_payloads"
    __table_args__ = (UniqueConstraint("payload_hash", name="uq_raw_payload_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    payload_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class NewsArticleTable(Base):
    __tablename__ = "news_articles"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_news_content_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    tickers_mentioned: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    assets_mentioned: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    raw_payload_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class SocialPostTable(Base):
    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    source_community: Mapped[str | None] = mapped_column(String(100), nullable=True)
    author_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tickers_mentioned: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    assets_mentioned: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    toxicity_or_spam_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw_payload_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class MacroIndicatorTable(Base):
    __tablename__ = "macro_indicators"
    __table_args__ = (
        UniqueConstraint("name", "timestamp", "source", name="uq_macro_indicator"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_payload_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FilingDocumentTable(Base):
    __tablename__ = "filing_documents"
    __table_args__ = (UniqueConstraint("accession_number", name="uq_filing_accession"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    filing_type: Mapped[str] = mapped_column(String(20), nullable=False)
    filed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    accession_number: Mapped[str] = mapped_column(String(50), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_items: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    raw_payload_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class SignalTable(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    horizon: Mapped[str] = mapped_column(String(20), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return_bucket: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_bucket: Mapped[str | None] = mapped_column(String(50), nullable=True)
    main_drivers_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    evidence_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    counterarguments: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    risk_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SourceReferenceTable(Base):
    __tablename__ = "source_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    topic_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    date_accessed: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PortfolioProfileTable(Base):
    __tablename__ = "portfolio_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    risk_bucket: Mapped[str] = mapped_column(String(30), nullable=False)
    time_horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)
    max_drawdown_tolerance: Mapped[float] = mapped_column(Float, nullable=False)
    use_crypto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    use_precious_metals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_liquidity_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avoid_leverage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    single_stock_soft_cap: Mapped[float] = mapped_column(Float, nullable=False, default=0.03)
    single_stock_hard_cap: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PortfolioPositionTable(Base):
    __tablename__ = "portfolio_positions"
    __table_args__ = (UniqueConstraint("profile_id", "symbol", name="uq_portfolio_position_profile_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolio_profiles.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_basis: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_weight: Mapped[float] = mapped_column(Float, nullable=False)
    asset_class: Mapped[str] = mapped_column(String(30), nullable=False)
    theme_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_speculative: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PortfolioPolicyRuleTable(Base):
    __tablename__ = "portfolio_policy_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolio_profiles.id"), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    soft_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    hard_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    asset_class: Mapped[str | None] = mapped_column(String(30), nullable=True)
    theme_tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ModelFeatureTable(Base):
    __tablename__ = "model_features"
    __table_args__ = (Index("ix_model_features_symbol_interval_timestamp", "symbol", "interval", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval: Mapped[str] = mapped_column(String(20), nullable=False, default="1d")
    features_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RiskEvaluationTable(Base):
    __tablename__ = "risk_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolio_profiles.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    violations_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    warnings_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    rationale_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    adjusted_recommendation: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DecisionOutputTable(Base):
    __tablename__ = "decision_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolio_profiles.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(30), nullable=False)
    portfolio_fit: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    allocation_impact_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    bull_case_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    bear_case_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    risk_flags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    evidence_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    invalidating_conditions_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="baseline_v1")
    human_review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    human_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BacktestRunTable(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    train_window: Mapped[str] = mapped_column(String(50), nullable=False)
    validation_window: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BacktestResultTable(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("backtest_runs.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(30), nullable=False)
    regime: Mapped[str] = mapped_column(String(50), nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    hit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_forward_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    sortino_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    false_positive_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLogTable(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TradeThesisTable(Base):
    __tablename__ = "trade_theses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    thesis_summary: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(20), nullable=False)
    entry_zone: Mapped[str | None] = mapped_column(String(200), nullable=True)
    invalidation_level: Mapped[str | None] = mapped_column(String(200), nullable=True)
    risk_reward_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    counterarguments: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DailyBriefingTable(Base):
    __tablename__ = "daily_briefings"
    __table_args__ = (UniqueConstraint("date", name="uq_daily_briefing_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    market_regime_summary: Mapped[str] = mapped_column(Text, nullable=False)
    macro_summary: Mapped[str] = mapped_column(Text, nullable=False)
    equity_summary: Mapped[str] = mapped_column(Text, nullable=False)
    etf_summary: Mapped[str] = mapped_column(Text, nullable=False)
    bond_summary: Mapped[str] = mapped_column(Text, nullable=False)
    crypto_summary: Mapped[str] = mapped_column(Text, nullable=False)
    top_opportunities: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    top_risks: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    unusual_social_activity: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    major_news_events: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    watchlist_changes: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    evidence_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AssetResearchReportTable(Base):
    __tablename__ = "asset_research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    current_context: Mapped[str] = mapped_column(Text, nullable=False)
    bullish_case: Mapped[str] = mapped_column(Text, nullable=False)
    bearish_case: Mapped[str] = mapped_column(Text, nullable=False)
    technical_context: Mapped[str] = mapped_column(Text, nullable=False)
    fundamental_context: Mapped[str] = mapped_column(Text, nullable=False)
    macro_context: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_context: Mapped[str] = mapped_column(Text, nullable=False)
    risk_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    suggested_next_steps: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
