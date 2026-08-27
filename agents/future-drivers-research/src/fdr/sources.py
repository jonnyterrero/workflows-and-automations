"""Source authority hierarchy, enforced in code.

The rule the platform lives or dies on: a Tier 5 source (Reddit, X, YouTube)
may cause the system to *investigate* an asset, but may never materially raise
a fundamental score without Tier 1-3 corroboration.

That rule is enforced here rather than in an agent prompt, because a prompt
instruction is a request and this needs to be a constraint. An agent that cites
only a forum post gets its score capped no matter how confidently it argues.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fdr.schemas import Evidence, SourceTier

# How much a tier is trusted to carry a fundamental claim.
TIER_AUTHORITY: dict[SourceTier, float] = {
    SourceTier.REGULATORY: 1.00,
    SourceTier.LICENSED: 0.85,
    SourceTier.JOURNALISM: 0.60,
    SourceTier.COMMENTARY: 0.30,
    SourceTier.SOCIAL: 0.05,
}

# Tiers 1-3 can establish fact. Tiers 4-5 generate hypotheses.
AUTHORITATIVE_TIERS = frozenset(
    {SourceTier.REGULATORY, SourceTier.LICENSED, SourceTier.JOURNALISM}
)

# A dimension supported only by commentary/social cannot exceed this, however
# persuasive the write-up. Set below the "advance to deeper research" bar so an
# uncorroborated idea can still be watchlisted but never promoted.
UNCORROBORATED_SCORE_CAP = 45.0

# Independent authoritative sources needed before breadth stops improving.
BREADTH_TARGET = 3

# Evidence freshness decay.
FRESH_DAYS = 90.0
STALE_DAYS = 730.0
UNKNOWN_DATE_FRESHNESS = 0.5


def _now() -> datetime:
    return datetime.now(tz=UTC)


def best_tier(evidence: list[Evidence]) -> SourceTier | None:
    """Most authoritative tier present, or None when there is no evidence."""
    if not evidence:
        return None
    return min((e.source_tier for e in evidence), key=lambda t: t.value)


def has_authoritative_support(evidence: list[Evidence]) -> bool:
    return any(e.source_tier in AUTHORITATIVE_TIERS for e in evidence)


def distinct_authoritative_sources(evidence: list[Evidence]) -> int:
    """Count independent authoritative sources.

    Deduplicated by source name so ten pulls from the same 10-K count once —
    one filing read five ways is one piece of evidence, not five.
    """
    return len({e.source_name.strip().lower() for e in evidence if e.source_tier in AUTHORITATIVE_TIERS})


def freshness_factor(evidence: Evidence, now: datetime | None = None) -> float:
    """1.0 for recent, decaying to 0.0 as evidence ages past ``STALE_DAYS``."""
    published = evidence.published_at
    if published is None:
        return UNKNOWN_DATE_FRESHNESS
    if published.tzinfo is None:
        published = published.replace(tzinfo=UTC)
    age_days = ((now or _now()) - published).total_seconds() / 86400.0
    if age_days <= FRESH_DAYS:
        return 1.0
    if age_days >= STALE_DAYS:
        return 0.0
    return 1.0 - (age_days - FRESH_DAYS) / (STALE_DAYS - FRESH_DAYS)


@dataclass(frozen=True)
class GateResult:
    score: float
    capped: bool
    reason: str


def gate_score(score: float, evidence: list[Evidence]) -> GateResult:
    """Clamp a claimed dimension score to what its evidence can support."""
    if not evidence:
        return GateResult(0.0, True, "No evidence supplied; dimension scored zero.")

    if not has_authoritative_support(evidence):
        tier = best_tier(evidence)
        tier_name = tier.name.title() if tier else "unknown"
        if score > UNCORROBORATED_SCORE_CAP:
            return GateResult(
                UNCORROBORATED_SCORE_CAP,
                True,
                (
                    f"Capped at {UNCORROBORATED_SCORE_CAP:.0f}: best available source is "
                    f"Tier {tier.value} ({tier_name}). Needs Tier 1-3 corroboration."
                ),
            )
        return GateResult(score, False, f"Uncorroborated (Tier {tier.value}) but scored below cap.")

    return GateResult(score, False, "Supported by Tier 1-3 evidence.")


def evidence_confidence(evidence: list[Evidence], now: datetime | None = None) -> float:
    """Confidence in the evidence base itself, 0-100.

    Deliberately independent of whether the evidence is favourable. A
    well-documented bear case scores high confidence too — this measures how
    much we trust what we know, not how much we like it.
    """
    if not evidence:
        return 0.0

    now = now or _now()
    authority = max(TIER_AUTHORITY[e.source_tier] for e in evidence)
    breadth = min(1.0, distinct_authoritative_sources(evidence) / BREADTH_TARGET)
    freshness = sum(freshness_factor(e, now) for e in evidence) / len(evidence)

    return round(100.0 * (0.50 * authority + 0.30 * breadth + 0.20 * freshness), 2)


def staleness_penalty(evidence: list[Evidence], now: datetime | None = None) -> float:
    """Penalty points (0-100) for operating on old evidence."""
    if not evidence:
        return 100.0
    now = now or _now()
    mean_freshness = sum(freshness_factor(e, now) for e in evidence) / len(evidence)
    return round(100.0 * (1.0 - mean_freshness), 2)


def source_weakness_penalty(evidence: list[Evidence]) -> float:
    """Penalty points (0-100) for leaning on weak sources."""
    if not evidence:
        return 100.0
    mean_authority = sum(TIER_AUTHORITY[e.source_tier] for e in evidence) / len(evidence)
    return round(100.0 * (1.0 - mean_authority), 2)


def partition_by_authority(
    evidence: list[Evidence],
) -> tuple[list[Evidence], list[Evidence]]:
    """Split into (authoritative, hypothesis-generating).

    Used by the narrative panel to route Tier 4-5 material away from the
    fundamental score and into its own display.
    """
    authoritative = [e for e in evidence if e.source_tier in AUTHORITATIVE_TIERS]
    hypothesis = [e for e in evidence if e.source_tier not in AUTHORITATIVE_TIERS]
    return authoritative, hypothesis
