"""Tests for deterministic investment-agent contracts and offline orchestration."""
from __future__ import annotations

import pytest

from packages.investment_agents.models import EvidenceItem, ResearchRequest, ResearchStatus
from packages.investment_agents.orchestrator import InvestmentResearchOrchestrator
from packages.investment_agents.tools import evidence_quality, overlap_risk


def sample_request() -> ResearchRequest:
    return ResearchRequest(
        symbol="nvda",
        asset_name="NVIDIA",
        theme="AI infrastructure",
        existing_positions=["VOO", "QQQM", "SMH"],
        evidence=[
            EvidenceItem(
                evidence_id="FILING-1",
                source_name="Fixture filing",
                source_type="primary_fixture",
                summary="Theme-linked demand increased.",
                reliability=0.9,
                freshness_days=10,
            ),
            EvidenceItem(
                evidence_id="EARNINGS-1",
                source_name="Fixture earnings",
                source_type="primary_fixture",
                summary="Backlog increased while competition remained material.",
                reliability=0.8,
                freshness_days=20,
            ),
        ],
    )


def test_request_normalizes_symbol_and_positions() -> None:
    request = sample_request()
    assert request.symbol == "NVDA"
    assert request.existing_positions == ["QQQM", "SMH", "VOO"]


def test_evidence_quality_is_bounded() -> None:
    result = evidence_quality(sample_request().evidence)
    assert result["count"] == 2
    assert 0 <= result["weighted_quality"] <= 100
    assert 0 <= result["freshness_penalty"] <= 100


def test_overlap_risk_detects_technology_concentration() -> None:
    result = overlap_risk("NVDA", ["VOO", "QQQM", "SMH"])
    assert result["score"] == 45.0
    assert result["overlapping_positions"] == ["QQQM", "SMH", "VOO"]


@pytest.mark.asyncio
async def test_offline_demo_returns_auditable_dossier() -> None:
    dossier = await InvestmentResearchOrchestrator().run_offline_demo(sample_request())
    assert dossier.symbol == "NVDA"
    assert dossier.research_status == ResearchStatus.VALUATION_GATED
    assert dossier.evidence_ids == ["FILING-1", "EARNINGS-1"]
    assert dossier.what_would_invalidate
    assert "human review" in dossier.disclaimer.lower()


@pytest.mark.asyncio
async def test_offline_demo_rejects_missing_evidence() -> None:
    request = ResearchRequest(symbol="TEST", asset_name="Test", theme="water infrastructure")
    dossier = await InvestmentResearchOrchestrator().run_offline_demo(request)
    assert dossier.research_status == ResearchStatus.EXPOSURE_UNPROVEN
    assert dossier.evidence_ids == []
