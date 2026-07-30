"""Deterministic tools used by the investment research agents."""
from __future__ import annotations

import json
from collections.abc import Iterable

from agents import function_tool

from packages.investment_agents.models import EvidenceItem, ResearchRequest


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def evidence_quality(evidence: Iterable[EvidenceItem]) -> dict[str, float | int]:
    """Calculate transparent evidence-quality statistics without model judgment."""
    rows = list(evidence)
    if not rows:
        return {"count": 0, "weighted_quality": 0.0, "freshness_penalty": 100.0}
    weighted = sum(item.reliability * max(0.2, 1 - item.freshness_days / 365) for item in rows)
    quality = 100 * weighted / len(rows)
    stale = sum(1 for item in rows if item.freshness_days > 120)
    return {
        "count": len(rows),
        "weighted_quality": _clamp(quality),
        "freshness_penalty": _clamp(100 * stale / len(rows)),
    }


def overlap_risk(symbol: str, existing_positions: list[str]) -> dict[str, float | list[str]]:
    """Calculate a conservative direct-overlap score from declared positions."""
    normalized = {item.upper().strip() for item in existing_positions}
    direct = symbol.upper() in normalized
    broad_tech = normalized.intersection({"VOO", "QQQ", "QQQM", "VGT", "XLK", "SMH", "SOXX"})
    score = 100.0 if direct else min(80.0, len(broad_tech) * 15.0)
    return {"score": score, "overlapping_positions": sorted(broad_tech)}


@function_tool
async def inspect_evidence_bundle(request_json: str) -> str:
    """Return the supplied evidence with deterministic quality and freshness statistics."""
    request = ResearchRequest.model_validate_json(request_json)
    payload = {
        "symbol": request.symbol,
        "theme": request.theme,
        "quality": evidence_quality(request.evidence),
        "evidence": [item.model_dump(mode="json") for item in request.evidence],
    }
    return json.dumps(payload, sort_keys=True)


@function_tool
async def calculate_portfolio_overlap(symbol: str, existing_positions_csv: str = "") -> str:
    """Estimate declared portfolio overlap; this does not perform ETF look-through."""
    positions = [item.strip() for item in existing_positions_csv.split(",") if item.strip()]
    return json.dumps(overlap_risk(symbol, positions), sort_keys=True)


@function_tool
async def calculate_transparent_score(
    business_quality: float,
    growth_durability: float,
    financial_strength: float,
    valuation: float,
    thematic_exposure: float,
    evidence_confidence: float,
    risk_score: float,
) -> str:
    """Calculate the documented long-term score and preserve every weighted contribution."""
    inputs = {
        "business_quality": _clamp(business_quality),
        "growth_durability": _clamp(growth_durability),
        "financial_strength": _clamp(financial_strength),
        "valuation": _clamp(valuation),
        "thematic_exposure": _clamp(thematic_exposure),
        "evidence_confidence": _clamp(evidence_confidence),
        "risk_score": _clamp(risk_score),
    }
    weights = {
        "business_quality": 0.20,
        "growth_durability": 0.20,
        "financial_strength": 0.15,
        "valuation": 0.20,
        "thematic_exposure": 0.10,
        "evidence_confidence": 0.15,
    }
    contributions = {key: round(inputs[key] * weight, 2) for key, weight in weights.items()}
    gross = sum(contributions.values())
    risk_penalty = round(inputs["risk_score"] * 0.20, 2)
    return json.dumps(
        {
            "inputs": inputs,
            "weights": weights,
            "contributions": contributions,
            "gross_score": round(gross, 2),
            "risk_penalty": risk_penalty,
            "net_score": _clamp(gross - risk_penalty),
        },
        sort_keys=True,
    )
