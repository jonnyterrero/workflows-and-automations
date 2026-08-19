"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_class", sa.String(30), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("symbol", "exchange", name="uq_assets_symbol_exchange"),
    )
    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("added_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("asset_id", name="uq_watchlist_asset"),
    )
    op.create_table(
        "raw_payloads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("payload_text", sa.Text(), nullable=True),
        sa.Column("parse_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.UniqueConstraint("payload_hash", name="uq_raw_payload_hash"),
    )
    op.create_table(
        "market_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Float(), nullable=True),
        sa.Column("high", sa.Float(), nullable=True),
        sa.Column("low", sa.Float(), nullable=True),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("interval", sa.String(10), nullable=False, server_default="1d"),
        sa.Column("raw_payload_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("asset_id", "timestamp", "interval", "source", name="uq_market_price"),
    )
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("tickers_mentioned", sa.JSON(), nullable=True),
        sa.Column("assets_mentioned", sa.JSON(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("credibility_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("raw_payload_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("content_hash", name="uq_news_content_hash"),
    )
    op.create_table(
        "social_posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("source_community", sa.String(100), nullable=True),
        sa.Column("author_hash", sa.String(64), nullable=False),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("tickers_mentioned", sa.JSON(), nullable=True),
        sa.Column("assets_mentioned", sa.JSON(), nullable=True),
        sa.Column("engagement_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("credibility_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("toxicity_or_spam_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("raw_payload_id", sa.Integer(), nullable=True),
    )
    op.create_table(
        "macro_indicators",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("raw_payload_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("name", "timestamp", "source", name="uq_macro_indicator"),
    )
    op.create_table(
        "filing_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_symbol", sa.String(20), nullable=False),
        sa.Column("filing_type", sa.String(20), nullable=False),
        sa.Column("filed_at", sa.DateTime(), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("accession_number", sa.String(50), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("risk_items", sa.JSON(), nullable=True),
        sa.Column("raw_payload_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("accession_number", name="uq_filing_accession"),
    )
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("horizon", sa.String(20), nullable=False),
        sa.Column("signal_type", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("counterarguments", sa.JSON(), nullable=True),
        sa.Column("risk_flags", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=False, server_default="system"),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "trade_theses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("thesis_summary", sa.Text(), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("time_horizon", sa.String(20), nullable=False),
        sa.Column("entry_zone", sa.String(200), nullable=True),
        sa.Column("invalidation_level", sa.String(200), nullable=True),
        sa.Column("risk_reward_notes", sa.Text(), nullable=True),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("counterarguments", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "daily_briefings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("market_regime_summary", sa.Text(), nullable=False),
        sa.Column("macro_summary", sa.Text(), nullable=False),
        sa.Column("equity_summary", sa.Text(), nullable=False),
        sa.Column("etf_summary", sa.Text(), nullable=False),
        sa.Column("bond_summary", sa.Text(), nullable=False),
        sa.Column("crypto_summary", sa.Text(), nullable=False),
        sa.Column("top_opportunities", sa.JSON(), nullable=True),
        sa.Column("top_risks", sa.JSON(), nullable=True),
        sa.Column("unusual_social_activity", sa.JSON(), nullable=True),
        sa.Column("major_news_events", sa.JSON(), nullable=True),
        sa.Column("watchlist_changes", sa.JSON(), nullable=True),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("date", name="uq_daily_briefing_date"),
    )
    op.create_table(
        "asset_research_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("current_context", sa.Text(), nullable=False),
        sa.Column("bullish_case", sa.Text(), nullable=False),
        sa.Column("bearish_case", sa.Text(), nullable=False),
        sa.Column("technical_context", sa.Text(), nullable=False),
        sa.Column("fundamental_context", sa.Text(), nullable=False),
        sa.Column("macro_context", sa.Text(), nullable=False),
        sa.Column("sentiment_context", sa.Text(), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=True),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("suggested_next_steps", sa.JSON(), nullable=True),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    for table in [
        "asset_research_reports", "daily_briefings", "trade_theses", "signals",
        "filing_documents", "macro_indicators", "social_posts", "news_articles",
        "market_prices", "raw_payloads", "watchlist", "assets",
    ]:
        op.drop_table(table)
