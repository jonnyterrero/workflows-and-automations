"""Typed research objects.

The asset dossier is the central record of the platform. Every agent reads and
writes this shape; nothing else crosses the agent boundary. Scores are produced
by ``fdr.scoring`` (deterministic code), never by an agent asserting a number.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class AssetClass(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    BOND_ETF = "bond_etf"
    CRYPTO = "crypto"
    COMMODITY_ETF = "commodity_etf"


class ResearchStatus(str, Enum):
    """Process states, not buy/sell calls.

    A status describes where a candidate sits in the research loop and what
    would move it, which is actionable in a way that "strong buy" is not.
    """

    ADVANCE_TO_DEEPER_RESEARCH = "advance_to_deeper_research"
    WATCHLIST_NEEDS_TRIGGER = "watchlist_needs_trigger"
    VALUATION_GATED = "valuation_gated"
    EXPOSURE_NOT_PROVEN = "exposure_not_proven"
    PORTFOLIO_OVERLAP_CONCERN = "portfolio_overlap_concern"
    RISK_EXCEEDS_REWARD = "risk_exceeds_reward"
    REJECT = "reject"


class ExposureStatus(str, Enum):
    PROVEN = "proven"
    PARTIAL = "partially_proven"
    UNPROVEN = "unproven"


class SourceTier(int, Enum):
    """Authority hierarchy. Lower is more authoritative.

    Tier 5 may cause the system to investigate an asset. It may never raise a
    fundamental score without Tier 1-3 corroboration; see ``fdr.sources``.
    """

    REGULATORY = 1  # SEC, Federal Reserve, Treasury, filings, issuer holdings
    LICENSED = 2  # Licensed market data, institutional research
    JOURNALISM = 3  # Established financial reporting
    COMMENTARY = 4  # Analyst commentary, specialist blogs
    SOCIAL = 5  # Reddit, X, YouTube, forums


class Evidence(BaseModel):
    """A single citation. Every scored claim must trace to one of these."""

    model_config = ConfigDict(extra="forbid")

    claim: str
    source_tier: SourceTier
    source_url: str | None = None
    source_name: str
    # Publication time and ingest time are tracked separately so a stale filing
    # surfaced by fresh reporting is not mistaken for fresh evidence.
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=_utcnow)
    excerpt: str | None = None

    @property
    def age_days(self) -> float | None:
        if self.published_at is None:
            return None
        published = self.published_at
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        return (_utcnow() - published).total_seconds() / 86400.0


class ThemeExposure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    exposure_status: ExposureStatus = ExposureStatus.UNPROVEN
    exposure_evidence: list[Evidence] = Field(default_factory=list)
    exposure_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    # Share of revenue the agent could actually tie to the theme, when the
    # filings support that arithmetic. None means "not disclosed", which is
    # different from zero and must not be scored as zero.
    revenue_share: float | None = Field(default=None, ge=0.0, le=1.0)


class ScoredDimension(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=100.0)
    evidence: list[Evidence] = Field(default_factory=list)
    notes: str | None = None


class Valuation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(default=50.0, ge=0.0, le=100.0)
    method: str = "peer_and_historical"
    expectations_summary: str = ""
    evidence: list[Evidence] = Field(default_factory=list)


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = ""
    key_drivers: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class PortfolioOverlap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Effective additional exposure this position would add once ETF holdings
    # are looked through, expressed 0-1 of the user's portfolio.
    effective_added_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    overlapping_holdings: list[str] = Field(default_factory=list)
    concentration_flags: list[str] = Field(default_factory=list)
    notes: str | None = None


class SourceFreshness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latest_filing_at: datetime | None = None
    latest_price_at: datetime | None = None
    latest_macro_at: datetime | None = None
    stale: bool = False


class Penalties(BaseModel):
    """Risk deductions, kept separate from the quality dimensions.

    Held apart so a high-quality, highly-levered company reads as exactly that
    rather than averaging into an unremarkable composite.
    """

    model_config = ConfigDict(extra="forbid")

    leverage: float = Field(default=0.0, ge=0.0, le=100.0)
    dilution: float = Field(default=0.0, ge=0.0, le=100.0)
    cyclicality: float = Field(default=0.0, ge=0.0, le=100.0)
    customer_concentration: float = Field(default=0.0, ge=0.0, le=100.0)
    regulatory: float = Field(default=0.0, ge=0.0, le=100.0)
    geographic: float = Field(default=0.0, ge=0.0, le=100.0)
    source_weakness: float = Field(default=0.0, ge=0.0, le=100.0)
    stale_data: float = Field(default=0.0, ge=0.0, le=100.0)
    crowded_expectations: float = Field(default=0.0, ge=0.0, le=100.0)

    def total(self) -> float:
        return float(sum(self.model_dump().values()))


class NarrativePanel(BaseModel):
    """Tier 5 sentiment, quarantined from the fundamental score.

    Social signal is useful for deciding *what to look at* and for spotting
    crowded positioning. It is reported beside the score, never inside it.
    """

    model_config = ConfigDict(extra="forbid")

    social_intensity: float | None = Field(default=None, ge=0.0, le=100.0)
    narrative_summary: str | None = None
    crowding_risk: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class ScoreCard(BaseModel):
    """Multi-dimensional output. There is deliberately no single headline."""

    model_config = ConfigDict(extra="forbid")

    quality: float = Field(ge=0.0, le=100.0)
    growth: float = Field(ge=0.0, le=100.0)
    valuation: float = Field(ge=0.0, le=100.0)
    financial_strength: float = Field(ge=0.0, le=100.0)
    evidence_confidence: float = Field(ge=0.0, le=100.0)
    risk: float = Field(ge=0.0, le=100.0)
    portfolio_fit: float = Field(ge=0.0, le=100.0)
    # Weighted roll-up, retained for ranking only. Never display without the
    # dimensions above.
    composite: float = Field(ge=0.0, le=100.0)


class AssetDossier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    asset_class: AssetClass
    research_status: ResearchStatus = ResearchStatus.EXPOSURE_NOT_PROVEN
    themes: list[ThemeExposure] = Field(default_factory=list)

    business_quality: ScoredDimension | None = None
    growth_durability: ScoredDimension | None = None
    financial_strength: ScoredDimension | None = None
    management: ScoredDimension | None = None
    catalysts: ScoredDimension | None = None
    valuation: Valuation | None = None

    bull_case: Scenario = Field(default_factory=Scenario)
    base_case: Scenario = Field(default_factory=Scenario)
    bear_case: Scenario = Field(default_factory=Scenario)

    first_rejection: str = ""
    what_would_make_it_investable: list[str] = Field(default_factory=list)
    what_would_invalidate: list[str] = Field(default_factory=list)

    portfolio_overlap: PortfolioOverlap = Field(default_factory=PortfolioOverlap)
    source_freshness: SourceFreshness = Field(default_factory=SourceFreshness)
    narrative_panel: NarrativePanel = Field(default_factory=NarrativePanel)
    penalties: Penalties = Field(default_factory=Penalties)
    scores: ScoreCard | None = None

    next_research_steps: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    as_of: datetime = Field(default_factory=_utcnow)

    @field_validator("symbol")
    @classmethod
    def _upper(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("symbol must not be empty")
        return v

    def all_evidence(self) -> list[Evidence]:
        found: list[Evidence] = []
        for theme in self.themes:
            found.extend(theme.exposure_evidence)
        for dim in (
            self.business_quality,
            self.growth_durability,
            self.financial_strength,
            self.management,
            self.catalysts,
        ):
            if dim is not None:
                found.extend(dim.evidence)
        if self.valuation is not None:
            found.extend(self.valuation.evidence)
        for case in (self.bull_case, self.base_case, self.bear_case):
            found.extend(case.evidence)
        return found


class Vote(str, Enum):
    RESEARCH = "research"
    WATCH = "watch"
    OWN = "own"
    AVOID = "avoid"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class DecisionJournalEntry(BaseModel):
    """Point-in-time record. This is the eventual ML training row.

    ``dossier_snapshot`` is stored verbatim so a future model can be trained on
    exactly the evidence that existed at decision time. Anything appended later
    (outcomes) is kept in separate fields to make look-ahead bias structurally
    hard rather than merely discouraged.
    """

    model_config = ConfigDict(extra="forbid")

    entry_id: str
    user_id: str
    symbol: str
    vote: Vote
    decided_at: datetime = Field(default_factory=_utcnow)

    what_was_believed: str
    supporting_evidence: list[Evidence] = Field(default_factory=list)
    risks_accepted: list[str] = Field(default_factory=list)
    expected_horizon_months: int | None = None
    invalidation_conditions: list[str] = Field(default_factory=list)
    dossier_snapshot: dict[str, Any] = Field(default_factory=dict)

    # Populated only by later review passes.
    outcome_reviewed_at: datetime | None = None
    thesis_validated: bool | None = None
    invalidation_occurred: bool | None = None
    forward_return: float | None = None
    benchmark_relative_return: float | None = None
    max_drawdown: float | None = None


class MaterialChange(BaseModel):
    """One detected delta since the previous review (the weekly-value engine)."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    field: str
    previous: Any = None
    current: Any = None
    direction: str = "changed"
    severity: str = "info"  # info | notable | critical
    description: str = ""
    invalidation_triggered: bool = False
    detected_at: datetime = Field(default_factory=_utcnow)
