"""Pydantic contracts shared by the four investment research agents."""
from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ResearchStatus(StrEnum):
    ADVANCE = "advance_to_deeper_research"
    WATCHLIST = "watchlist_needs_trigger"
    VALUATION_GATED = "valuation_gated"
    EXPOSURE_UNPROVEN = "exposure_not_proven"
    OVERLAP_CONCERN = "portfolio_overlap_concern"
    RISK_EXCEEDS_REWARD = "risk_exceeds_reward"
    REJECT = "reject"


class ExposureStatus(StrEnum):
    PROVEN = "proven"
    PARTIAL = "partially_proven"
    UNPROVEN = "unproven"


class EvidenceItem(BaseModel):
    evidence_id: str
    source_name: str
    source_type: str
    source_url: str | None = None
    published_at: str | None = None
    summary: str
    reliability: float = Field(ge=0.0, le=1.0)
    freshness_days: int = Field(default=0, ge=0)


class ResearchRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    asset_name: str = Field(min_length=1, max_length=160)
    asset_class: str = Field(default="stock")
    theme: str = Field(min_length=2, max_length=160)
    horizon_years: int = Field(default=5, ge=1, le=30)
    existing_positions: list[str] = Field(default_factory=list)
    question: str = Field(default="Evaluate whether this asset deserves deeper long-term research.")
    evidence: list[EvidenceItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_symbol(self) -> "ResearchRequest":
        self.symbol = self.symbol.upper().strip()
        self.existing_positions = sorted({item.upper().strip() for item in self.existing_positions if item.strip()})
        return self


class CandidateIdea(BaseModel):
    symbol: str
    asset_name: str
    beneficiary_pathway: str
    why_now: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class ThemeScoutReport(BaseModel):
    theme: str
    theme_summary: str
    structural_drivers: list[str]
    candidate: CandidateIdea
    competing_beneficiaries: list[str] = Field(default_factory=list)
    hype_or_crowding_flags: list[str] = Field(default_factory=list)


class EvidenceAnalystReport(BaseModel):
    symbol: str
    exposure_status: ExposureStatus
    exposure_confidence: float = Field(ge=0.0, le=1.0)
    verified_evidence: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    business_quality_score: float = Field(ge=0.0, le=100.0)
    growth_durability_score: float = Field(ge=0.0, le=100.0)
    financial_strength_score: float = Field(ge=0.0, le=100.0)
    data_gaps: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class RiskValuationReport(BaseModel):
    symbol: str
    valuation_score: float = Field(ge=0.0, le=100.0)
    risk_score: float = Field(ge=0.0, le=100.0)
    portfolio_overlap_score: float = Field(ge=0.0, le=100.0)
    embedded_expectations: list[str] = Field(default_factory=list)
    top_risks: list[str] = Field(default_factory=list)
    bull_case: str
    base_case: str
    bear_case: str
    what_would_make_it_investable: list[str] = Field(default_factory=list)
    what_would_invalidate: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ScoreCard(BaseModel):
    business_quality: float = Field(ge=0.0, le=100.0)
    growth_durability: float = Field(ge=0.0, le=100.0)
    financial_strength: float = Field(ge=0.0, le=100.0)
    valuation: float = Field(ge=0.0, le=100.0)
    thematic_exposure: float = Field(ge=0.0, le=100.0)
    evidence_confidence: float = Field(ge=0.0, le=100.0)
    risk: float = Field(ge=0.0, le=100.0)
    portfolio_fit: float = Field(ge=0.0, le=100.0)


class InvestmentCommitteeDossier(BaseModel):
    symbol: str
    asset_name: str
    asset_class: str
    theme: str
    research_status: ResearchStatus
    committee_summary: str
    scorecard: ScoreCard
    first_rejection: str | None = None
    bull_case: str
    base_case: str
    bear_case: str
    what_would_make_it_investable: list[str]
    what_would_invalidate: list[str]
    next_research_steps: list[str]
    evidence_ids: list[str]
    unresolved_questions: list[str]
    as_of: date = Field(default_factory=date.today)
    disclaimer: str = (
        "Research and decision-support only. Not personalized financial, legal, or tax advice. "
        "All conclusions require human review."
    )

    @model_validator(mode="after")
    def ensure_evidence_for_positive_status(self) -> "InvestmentCommitteeDossier":
        if self.research_status == ResearchStatus.ADVANCE and not self.evidence_ids:
            raise ValueError("advance_to_deeper_research requires at least one evidence ID")
        return self
