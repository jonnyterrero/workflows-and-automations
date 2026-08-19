"""Change detection: what materially moved since the last review.

This is the feature that makes the platform worth opening weekly. "Give me
today's best stocks" is a question with no stable answer; "guidance was cut and
your stated invalidation condition just fired" is one worth a notification.

Invalidation checks run first, because a thesis the user themselves said would
be broken by event X is the highest-value alert the system can produce.
"""
from __future__ import annotations

from typing import Any

from fdr.schemas import AssetDossier, MaterialChange

# Dimensions worth alerting on, and how far they must move to be notable.
_SCORE_FIELDS: dict[str, float] = {
    "quality": 5.0,
    "growth": 5.0,
    "valuation": 8.0,
    "financial_strength": 5.0,
    "risk": 5.0,
    "portfolio_fit": 10.0,
    "evidence_confidence": 10.0,
}

_PENALTY_FIELDS: dict[str, float] = {
    "leverage": 10.0,
    "dilution": 10.0,
    "cyclicality": 10.0,
    "customer_concentration": 10.0,
    "regulatory": 10.0,
    "geographic": 10.0,
    "crowded_expectations": 10.0,
}

_CRITICAL_THRESHOLD = 15.0


def _direction(previous: float, current: float) -> str:
    if current > previous:
        return "increased"
    if current < previous:
        return "decreased"
    return "unchanged"


def _severity(delta: float, threshold: float) -> str:
    if abs(delta) >= max(threshold * 2, _CRITICAL_THRESHOLD):
        return "critical"
    if abs(delta) >= threshold:
        return "notable"
    return "info"


def detect_changes(
    previous: AssetDossier, current: AssetDossier
) -> list[MaterialChange]:
    """Compare two dossier states and return what materially moved."""
    if previous.symbol != current.symbol:
        raise ValueError(
            f"cannot compare different symbols: {previous.symbol} vs {current.symbol}"
        )

    changes: list[MaterialChange] = []
    symbol = current.symbol

    # 1. Invalidation conditions the user wrote down, now observed.
    prior_conditions = {c.strip().lower() for c in previous.what_would_invalidate}
    for condition in prior_conditions:
        if _condition_appears_met(condition, current):
            changes.append(
                MaterialChange(
                    symbol=symbol,
                    field="what_would_invalidate",
                    previous=condition,
                    current="observed",
                    direction="triggered",
                    severity="critical",
                    invalidation_triggered=True,
                    description=(
                        f"Stated invalidation condition appears met: {condition}"
                    ),
                )
            )

    # 2. Research status transition.
    if previous.research_status != current.research_status:
        changes.append(
            MaterialChange(
                symbol=symbol,
                field="research_status",
                previous=previous.research_status.value,
                current=current.research_status.value,
                direction="changed",
                severity="notable",
                description=(
                    f"Research status moved from {previous.research_status.value} "
                    f"to {current.research_status.value}."
                ),
            )
        )

    # 3. Score movement.
    if previous.scores and current.scores:
        for field, threshold in _SCORE_FIELDS.items():
            before = getattr(previous.scores, field)
            after = getattr(current.scores, field)
            delta = after - before
            if abs(delta) < threshold:
                continue
            changes.append(
                MaterialChange(
                    symbol=symbol,
                    field=f"scores.{field}",
                    previous=before,
                    current=after,
                    direction=_direction(before, after),
                    severity=_severity(delta, threshold),
                    description=(
                        f"{field.replace('_', ' ').title()} {_direction(before, after)} "
                        f"{abs(delta):.1f} points ({before:.0f} to {after:.0f})."
                    ),
                )
            )

    # 4. Risk penalties.
    for field, threshold in _PENALTY_FIELDS.items():
        before = getattr(previous.penalties, field)
        after = getattr(current.penalties, field)
        delta = after - before
        if abs(delta) < threshold:
            continue
        changes.append(
            MaterialChange(
                symbol=symbol,
                field=f"penalties.{field}",
                previous=before,
                current=after,
                direction=_direction(before, after),
                severity=_severity(delta, threshold),
                description=(
                    f"{field.replace('_', ' ').title()} risk "
                    f"{_direction(before, after)} by {abs(delta):.0f} points."
                ),
            )
        )

    # 5. Theme exposure re-grading — the Evidence Analyst changing its mind
    #    about whether exposure is real is a first-class event.
    prior_themes = {t.name: t for t in previous.themes}
    for theme in current.themes:
        prior = prior_themes.get(theme.name)
        if prior is None:
            changes.append(
                MaterialChange(
                    symbol=symbol, field=f"themes.{theme.name}",
                    previous=None, current=theme.exposure_status.value,
                    direction="added", severity="info",
                    description=f"New theme tracked: {theme.name} ({theme.exposure_status.value}).",
                )
            )
        elif prior.exposure_status != theme.exposure_status:
            changes.append(
                MaterialChange(
                    symbol=symbol, field=f"themes.{theme.name}",
                    previous=prior.exposure_status.value,
                    current=theme.exposure_status.value,
                    direction="changed", severity="notable",
                    description=(
                        f"Theme exposure for {theme.name} re-graded from "
                        f"{prior.exposure_status.value} to {theme.exposure_status.value}."
                    ),
                )
            )

    # 6. Evidence going stale is itself a change worth surfacing.
    if not previous.source_freshness.stale and current.source_freshness.stale:
        changes.append(
            MaterialChange(
                symbol=symbol, field="source_freshness.stale",
                previous=False, current=True,
                direction="changed", severity="notable",
                description="Underlying evidence is now stale; refresh before relying on this dossier.",
            )
        )

    order = {"critical": 0, "notable": 1, "info": 2}
    changes.sort(key=lambda c: order.get(c.severity, 3))
    return changes


def _condition_appears_met(condition: str, current: AssetDossier) -> bool:
    """Conservative textual check against the current dossier's own findings.

    Deliberately narrow: it only fires when the agents have independently
    written the same concern into the bear case, first rejection, or open
    questions. Prefers missing a trigger over crying wolf, since a
    false-positive invalidation alert would teach users to ignore the channel.
    """
    haystack = " ".join(
        [
            current.bear_case.summary,
            " ".join(current.bear_case.key_drivers),
            current.first_rejection,
            " ".join(current.open_questions),
        ]
    ).lower()

    tokens = [t for t in condition.split() if len(t) > 4]
    if len(tokens) < 2:
        return False
    matched = sum(1 for token in tokens if token in haystack)
    return matched >= max(2, len(tokens) // 2)


def summarize_changes(changes: list[MaterialChange]) -> dict[str, Any]:
    """Roll up for the daily brief."""
    return {
        "total": len(changes),
        "critical": sum(1 for c in changes if c.severity == "critical"),
        "notable": sum(1 for c in changes if c.severity == "notable"),
        "invalidations_triggered": sum(1 for c in changes if c.invalidation_triggered),
        "changes": [c.model_dump(mode="json") for c in changes],
    }
