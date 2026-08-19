"""Pydantic models for portfolio policy evaluation."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PortfolioRiskBucket(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class PortfolioAssetClass(str, Enum):
    ETF = "ETF"
    EQUITY = "EQUITY"
    CRYPTO = "CRYPTO"
    BOND = "BOND"
    CASH_EQUIVALENT = "CASH_EQUIVALENT"
    COMMODITY = "COMMODITY"
    METAL = "METAL"
    FUND = "FUND"
    OTHER = "OTHER"


class PortfolioRiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    SEVERE = "severe"


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


class PortfolioSignalDirection(str, Enum):
    STRONG_NEGATIVE = "strong_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    STRONG_POSITIVE = "strong_positive"


class AssetCandidate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    symbol: str
    name: str
    asset_class: PortfolioAssetClass
    theme_tags: list[str] = Field(default_factory=list)
    sector: str | None = None
    is_speculative: bool = False


class PortfolioProfile(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: int | None = None
    name: str
    risk_bucket: PortfolioRiskBucket
    time_horizon_years: int = Field(ge=1)
    max_drawdown_tolerance: float = Field(ge=0.0, le=1.0)
    use_crypto: bool = True
    use_precious_metals: bool = True
    min_liquidity_months: int = Field(ge=0)
    avoid_leverage: bool = True
    single_stock_soft_cap: float = Field(ge=0.0, le=1.0)
    single_stock_hard_cap: float = Field(ge=0.0, le=1.0)
    notes: str | None = None


class PortfolioPosition(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    symbol: str
    asset_class: PortfolioAssetClass
    portfolio_weight: float = Field(ge=0.0, le=1.0)
    quantity: float | None = None
    market_value: float | None = None
    cost_basis: float | None = None
    theme_tags: list[str] = Field(default_factory=list)
    is_speculative: bool = False


class MacroRegime(BaseModel):
    growth_regime: str = "expansion"
    inflation_regime: str = "disinflationary"
    rate_regime: str = "moderately_restrictive"
    liquidity_regime: str = "neutral"
    risk_sentiment: str = "risk_on"
    stale_data: bool = False


class PolicyRule(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    rule_name: str
    rule_type: Literal[
        "asset_class_cap",
        "asset_class_minimum",
        "theme_cap",
        "theme_target",
        "single_position_cap",
        "single_position_target",
        "speculative_cap",
    ]
    target_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    soft_cap: float | None = Field(default=None, ge=0.0, le=1.0)
    hard_cap: float | None = Field(default=None, ge=0.0, le=1.0)
    minimum_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    asset_class: PortfolioAssetClass | None = None
    theme_tag: str | None = None
    symbol: str | None = None
    is_active: bool = True


class SignalOutput(BaseModel):
    symbol: str
    signal: PortfolioSignalDirection
    confidence: float = Field(ge=0.0, le=1.0)
    expected_return_bucket: str | None = None
    risk_bucket: str | None = None
    main_drivers_json: dict[str, Any] = Field(default_factory=dict)
    model_version: str = "baseline_v1"


class PortfolioDecisionInput(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    profile: PortfolioProfile
    current_positions: list[PortfolioPosition]
    proposed_asset: AssetCandidate
    proposed_weight: float = Field(ge=0.0, le=1.0)
    macro_regime: MacroRegime
    model_signal: SignalOutput | None = None
    policy_rules: list[PolicyRule]
    data_is_stale: bool = False
    above_sma200: bool | None = None
    as_of: datetime | None = None


class RiskEvaluationResult(BaseModel):
    allowed: bool
    decision: PolicyDecision
    riskLevel: PortfolioRiskLevel
    violations: list[str]
    warnings: list[str]
    rationale: list[str]
    adjustedRecommendation: str


class DecisionOutput(BaseModel):
    decisionId: str
    symbol: str
    assetClass: PortfolioAssetClass
    decision: str
    action: str
    confidence: float
    timeHorizon: str
    portfolioFit: str
    riskLevel: PortfolioRiskLevel
    allocationImpact: dict[str, Any]
    bullCase: list[str]
    bearCase: list[str]
    riskFlags: list[str]
    evidence: list[dict[str, Any]]
    invalidatingConditions: list[str]
    modelVersion: str
    createdAt: datetime
