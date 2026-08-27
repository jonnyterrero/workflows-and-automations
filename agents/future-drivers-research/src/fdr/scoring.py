"""Deterministic scoring.

Agents supply evidence and judgement; this module supplies every number. No
agent is trusted to emit a score, because a score asserted by a language model
is an opinion wearing a number's clothing.

Two design rules from the brief are load-bearing here:

1. Nothing collapses to a single figure. ``ScoreCard`` carries seven dimensions
   because "85 quality / 25 valuation" tells you what to do and "73" does not.
2. Penalties are deducted, never averaged. A levered, cyclical business with a
   great moat should read as exactly that.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from fdr import sources
from fdr.schemas import (
    AssetDossier,
    ExposureStatus,
    Penalties,
    PortfolioOverlap,
    ResearchStatus,
    ScoreCard,
    ScoredDimension,
)


@dataclass(frozen=True)
class Weights:
    """Long-term equity weights.

    News, technical momentum, and social sentiment are absent by design — they
    belong to the narrative panel, not the fundamental score.
    """

    business_quality: float = 0.20
    growth_durability: float = 0.20
    valuation: float = 0.20
    financial_strength: float = 0.15
    proven_exposure: float = 0.10
    management: float = 0.10
    catalysts: float = 0.05

    def validate(self) -> None:
        total = sum(asdict(self).values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weights must sum to 1.0, got {total}")


DEFAULT_WEIGHTS = Weights()

# Exposure quality translated to points.
EXPOSURE_POINTS: dict[ExposureStatus, float] = {
    ExposureStatus.PROVEN: 100.0,
    ExposureStatus.PARTIAL: 50.0,
    ExposureStatus.UNPROVEN: 0.0,
}

# Overlap beyond this share of the portfolio drives portfolio fit to zero.
OVERLAP_SATURATION = 0.25
NEUTRAL_WHEN_UNKNOWN = 50.0


@dataclass(frozen=True)
class StatusThresholds:
    advance_composite: float = 65.0
    advance_evidence_confidence: float = 60.0
    reject_composite: float = 35.0
    valuation_gate: float = 40.0
    strong_fundamentals: float = 60.0
    risk_floor: float = 40.0
    overlap_floor: float = 35.0
    exposure_confidence_floor: float = 0.35


DEFAULT_THRESHOLDS = StatusThresholds()


def _dimension_score(dim: ScoredDimension | None) -> float:
    """Score a dimension, clamped to what its evidence can carry."""
    if dim is None:
        return 0.0
    return sources.gate_score(dim.score, dim.evidence).score


def exposure_score(dossier: AssetDossier) -> float:
    """Proven thematic exposure, weighted by the agent's stated confidence.

    Unproven exposure contributes nothing rather than a small positive. An
    attractive theme a company merely talks about is worth zero.
    """
    if not dossier.themes:
        return 0.0

    best = 0.0
    for theme in dossier.themes:
        points = EXPOSURE_POINTS[theme.exposure_status]
        gated = sources.gate_score(points, theme.exposure_evidence).score
        best = max(best, gated * theme.exposure_confidence)
    return round(best, 2)


def portfolio_fit_score(overlap: PortfolioOverlap) -> float:
    """How much genuinely new exposure this adds to the user's portfolio."""
    if overlap.effective_added_weight is None:
        base = NEUTRAL_WHEN_UNKNOWN
    else:
        saturation = min(1.0, overlap.effective_added_weight / OVERLAP_SATURATION)
        base = 100.0 * (1.0 - saturation)

    # Each named concentration flag is a concrete, already-identified problem.
    base -= 10.0 * len(overlap.concentration_flags)
    return round(max(0.0, min(100.0, base)), 2)


def compute_penalties(
    dossier: AssetDossier, now: datetime | None = None
) -> Penalties:
    """Fill the evidence-derived penalties; preserve agent-supplied ones.

    Leverage, dilution, cyclicality and the rest are the Risk Analyst's
    judgement. Source weakness and staleness are properties of the evidence
    base itself, so we compute them rather than ask.
    """
    evidence = dossier.all_evidence()
    supplied = dossier.penalties
    return Penalties(
        leverage=supplied.leverage,
        dilution=supplied.dilution,
        cyclicality=supplied.cyclicality,
        customer_concentration=supplied.customer_concentration,
        regulatory=supplied.regulatory,
        geographic=supplied.geographic,
        crowded_expectations=supplied.crowded_expectations,
        source_weakness=sources.source_weakness_penalty(evidence),
        stale_data=sources.staleness_penalty(evidence, now),
    )


def risk_score(penalties: Penalties) -> float:
    """0-100 where 100 is low risk.

    Penalties are averaged across the nine categories rather than summed, so a
    single flagged risk doesn't zero the score, but several compound.
    """
    values = list(penalties.model_dump().values())
    mean_penalty = sum(values) / len(values)
    return round(max(0.0, 100.0 - mean_penalty), 2)


def score_dossier(
    dossier: AssetDossier,
    weights: Weights = DEFAULT_WEIGHTS,
    now: datetime | None = None,
) -> ScoreCard:
    weights.validate()

    quality = _dimension_score(dossier.business_quality)
    growth = _dimension_score(dossier.growth_durability)
    strength = _dimension_score(dossier.financial_strength)
    management = _dimension_score(dossier.management)
    catalysts = _dimension_score(dossier.catalysts)
    exposure = exposure_score(dossier)

    if dossier.valuation is None:
        valuation = 0.0
    else:
        valuation = sources.gate_score(
            dossier.valuation.score, dossier.valuation.evidence
        ).score

    penalties = compute_penalties(dossier, now)
    risk = risk_score(penalties)
    fit = portfolio_fit_score(dossier.portfolio_overlap)
    confidence = sources.evidence_confidence(dossier.all_evidence(), now)

    weighted = (
        weights.business_quality * quality
        + weights.growth_durability * growth
        + weights.valuation * valuation
        + weights.financial_strength * strength
        + weights.proven_exposure * exposure
        + weights.management * management
        + weights.catalysts * catalysts
    )

    # Risk scales the roll-up rather than being averaged into it, so risk can
    # never be offset by a strong quality score.
    composite = weighted * (risk / 100.0)

    return ScoreCard(
        quality=round(quality, 2),
        growth=round(growth, 2),
        valuation=round(valuation, 2),
        financial_strength=round(strength, 2),
        evidence_confidence=confidence,
        risk=risk,
        portfolio_fit=fit,
        composite=round(max(0.0, min(100.0, composite)), 2),
    )


def assign_status(
    dossier: AssetDossier,
    scores: ScoreCard,
    thresholds: StatusThresholds = DEFAULT_THRESHOLDS,
) -> ResearchStatus:
    """Map scores to a process state.

    Gates are ordered most-disqualifying first, so the returned status names
    the binding constraint. A cheap company with unproven theme exposure comes
    back ``exposure_not_proven``, which is the thing to go fix.
    """
    proven = any(
        t.exposure_status is ExposureStatus.PROVEN
        and t.exposure_confidence >= thresholds.exposure_confidence_floor
        for t in dossier.themes
    )
    if not proven:
        return ResearchStatus.EXPOSURE_NOT_PROVEN

    if scores.risk < thresholds.risk_floor:
        return ResearchStatus.RISK_EXCEEDS_REWARD

    if scores.portfolio_fit < thresholds.overlap_floor:
        return ResearchStatus.PORTFOLIO_OVERLAP_CONCERN

    fundamentals_strong = (
        scores.quality >= thresholds.strong_fundamentals
        and scores.growth >= thresholds.strong_fundamentals
    )
    if scores.valuation < thresholds.valuation_gate and fundamentals_strong:
        # Good business, price already reflects it. Worth tracking, not buying.
        return ResearchStatus.VALUATION_GATED

    if scores.composite < thresholds.reject_composite:
        return ResearchStatus.REJECT

    if (
        scores.composite >= thresholds.advance_composite
        and scores.evidence_confidence >= thresholds.advance_evidence_confidence
    ):
        return ResearchStatus.ADVANCE_TO_DEEPER_RESEARCH

    return ResearchStatus.WATCHLIST_NEEDS_TRIGGER


def finalize(
    dossier: AssetDossier,
    weights: Weights = DEFAULT_WEIGHTS,
    thresholds: StatusThresholds = DEFAULT_THRESHOLDS,
    now: datetime | None = None,
) -> AssetDossier:
    """Attach computed scores, penalties, and status to a dossier."""
    penalties = compute_penalties(dossier, now)
    scores = score_dossier(dossier, weights, now)
    status = assign_status(dossier, scores, thresholds)

    updated = dossier.model_copy(deep=True)
    updated.penalties = penalties
    updated.scores = scores
    updated.research_status = status

    # Route Tier 4-5 material into the narrative panel so it is visible as
    # context without ever having touched the fundamental score.
    _, hypothesis = sources.partition_by_authority(dossier.all_evidence())
    if hypothesis and not updated.narrative_panel.evidence:
        updated.narrative_panel.evidence = hypothesis
    return updated


def explain(scores: ScoreCard) -> str:
    """One-line summary for briefs and alerts."""
    return (
        f"quality {scores.quality:.0f} | growth {scores.growth:.0f} | "
        f"valuation {scores.valuation:.0f} | strength {scores.financial_strength:.0f} | "
        f"risk {scores.risk:.0f} | fit {scores.portfolio_fit:.0f} | "
        f"evidence {scores.evidence_confidence:.0f}"
    )
