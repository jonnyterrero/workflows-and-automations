"""Add portfolio policy foundation tables and compatibility columns.

Revision ID: 002
Revises: 001
Create Date: 2026-06-14
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("theme_tags", sa.JSON(), nullable=True))

    op.add_column("market_prices", sa.Column("symbol", sa.String(length=50), nullable=True))
    op.add_column("market_prices", sa.Column("adjusted_close", sa.Float(), nullable=True))
    op.add_column(
        "market_prices",
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        "ix_market_prices_asset_interval_timestamp",
        "market_prices",
        ["asset_id", "interval", "timestamp"],
        unique=False,
    )

    op.add_column("signals", sa.Column("symbol", sa.String(length=50), nullable=True))
    op.add_column("signals", sa.Column("expected_return_bucket", sa.String(length=50), nullable=True))
    op.add_column("signals", sa.Column("risk_bucket", sa.String(length=50), nullable=True))
    op.add_column("signals", sa.Column("main_drivers_json", sa.JSON(), nullable=True))

    op.create_table(
        "source_references",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("topic_tags", sa.JSON(), nullable=True),
        sa.Column("credibility_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("date_accessed", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "portfolio_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("risk_bucket", sa.String(length=30), nullable=False),
        sa.Column("time_horizon_years", sa.Integer(), nullable=False),
        sa.Column("max_drawdown_tolerance", sa.Float(), nullable=False),
        sa.Column("use_crypto", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("use_precious_metals", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("min_liquidity_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avoid_leverage", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("single_stock_soft_cap", sa.Float(), nullable=False, server_default="0.03"),
        sa.Column("single_stock_hard_cap", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "portfolio_positions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("portfolio_profiles.id"), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("market_value", sa.Float(), nullable=True),
        sa.Column("cost_basis", sa.Float(), nullable=True),
        sa.Column("portfolio_weight", sa.Float(), nullable=False),
        sa.Column("asset_class", sa.String(length=30), nullable=False),
        sa.Column("theme_tags", sa.JSON(), nullable=True),
        sa.Column("is_speculative", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("profile_id", "symbol", name="uq_portfolio_position_profile_symbol"),
    )

    op.create_table(
        "portfolio_policy_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("portfolio_profiles.id"), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("target_weight", sa.Float(), nullable=True),
        sa.Column("soft_cap", sa.Float(), nullable=True),
        sa.Column("hard_cap", sa.Float(), nullable=True),
        sa.Column("minimum_weight", sa.Float(), nullable=True),
        sa.Column("asset_class", sa.String(length=30), nullable=True),
        sa.Column("theme_tag", sa.String(length=100), nullable=True),
        sa.Column("symbol", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "model_features",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("interval", sa.String(length=20), nullable=False, server_default="1d"),
        sa.Column("features_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        "ix_model_features_symbol_interval_timestamp",
        "model_features",
        ["symbol", "interval", "timestamp"],
        unique=False,
    )

    op.create_table(
        "risk_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("portfolio_profiles.id"), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("violations_json", sa.JSON(), nullable=True),
        sa.Column("warnings_json", sa.JSON(), nullable=True),
        sa.Column("rationale_json", sa.JSON(), nullable=True),
        sa.Column("adjusted_recommendation", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "decision_outputs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("portfolio_profiles.id"), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("time_horizon", sa.String(length=30), nullable=False),
        sa.Column("portfolio_fit", sa.String(length=100), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("allocation_impact_json", sa.JSON(), nullable=True),
        sa.Column("bull_case_json", sa.JSON(), nullable=True),
        sa.Column("bear_case_json", sa.JSON(), nullable=True),
        sa.Column("risk_flags_json", sa.JSON(), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("invalidating_conditions_json", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=False, server_default="baseline_v1"),
        sa.Column("human_review_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("human_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("train_window", sa.String(length=50), nullable=False),
        sa.Column("validation_window", sa.String(length=50), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "backtest_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("backtest_run_id", sa.Integer(), sa.ForeignKey("backtest_runs.id"), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("asset_class", sa.String(length=30), nullable=False),
        sa.Column("regime", sa.String(length=50), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1", sa.Float(), nullable=True),
        sa.Column("hit_rate", sa.Float(), nullable=True),
        sa.Column("average_forward_return", sa.Float(), nullable=True),
        sa.Column("max_drawdown", sa.Float(), nullable=True),
        sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        sa.Column("sortino_ratio", sa.Float(), nullable=True),
        sa.Column("false_positive_rate", sa.Float(), nullable=True),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("backtest_results")
    op.drop_table("backtest_runs")
    op.drop_table("decision_outputs")
    op.drop_table("risk_evaluations")
    op.drop_index("ix_model_features_symbol_interval_timestamp", table_name="model_features")
    op.drop_table("model_features")
    op.drop_table("portfolio_policy_rules")
    op.drop_table("portfolio_positions")
    op.drop_table("portfolio_profiles")
    op.drop_table("source_references")

    op.drop_column("signals", "main_drivers_json")
    op.drop_column("signals", "risk_bucket")
    op.drop_column("signals", "expected_return_bucket")
    op.drop_column("signals", "symbol")

    op.drop_index("ix_market_prices_asset_interval_timestamp", table_name="market_prices")
    op.drop_column("market_prices", "ingested_at")
    op.drop_column("market_prices", "adjusted_close")
    op.drop_column("market_prices", "symbol")

    op.drop_column("assets", "theme_tags")
