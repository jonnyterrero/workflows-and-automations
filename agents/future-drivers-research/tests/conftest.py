"""Shared fixtures.

Every test runs in demo mode against a temporary data directory, so the suite
never touches the network and never writes to a real dossier store.
"""
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest

os.environ.setdefault("FDR_DEMO_MODE", "true")

from fdr import config  # noqa: E402
from fdr.schemas import (  # noqa: E402
    AssetClass,
    AssetDossier,
    Evidence,
    ExposureStatus,
    ScoredDimension,
    SourceTier,
    ThemeExposure,
    Valuation,
)

# Captured before the autouse fixture stubs it out, so the tests that exercise
# .env parsing itself can still reach the real implementation.
_REAL_LOAD_DOTENV = config.load_dotenv


@pytest.fixture
def real_load_dotenv():
    return _REAL_LOAD_DOTENV


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Isolate every test from the developer's real configuration.

    ``load_dotenv`` is stubbed out because a populated .env would otherwise
    hand tests live credentials and agent IDs — which once made a precondition
    test open a real session and hang instead of failing fast.
    """
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)
    for leaked in ("ANTHROPIC_API_KEY", "FDR_COMMITTEE_AGENT_ID", "FDR_ENVIRONMENT_ID"):
        monkeypatch.delenv(leaked, raising=False)
    monkeypatch.setenv("FDR_DEMO_MODE", "true")
    monkeypatch.setenv("FDR_DATA_DIR", str(tmp_path / "data"))
    config.get_settings(refresh=True)
    yield
    config.get_settings(refresh=True)


def make_evidence(
    tier: SourceTier = SourceTier.REGULATORY,
    name: str = "SEC 10-K",
    age_days: int = 30,
    claim: str = "Data centre revenue disclosed at 87% of total.",
) -> Evidence:
    return Evidence(
        claim=claim,
        source_tier=tier,
        source_name=name,
        source_url="https://www.sec.gov/example",
        published_at=datetime.now(tz=UTC) - timedelta(days=age_days),
    )


@pytest.fixture
def filing_evidence() -> Evidence:
    return make_evidence()


@pytest.fixture
def strong_dossier() -> AssetDossier:
    """A well-evidenced candidate that should clear the gates."""
    ev = [
        make_evidence(name="SEC 10-K"),
        make_evidence(name="SEC 10-Q", age_days=20),
        make_evidence(tier=SourceTier.LICENSED, name="Market data vendor", age_days=1),
    ]
    return AssetDossier(
        symbol="ETN",
        asset_class=AssetClass.STOCK,
        themes=[
            ThemeExposure(
                name="grid_modernization",
                exposure_status=ExposureStatus.PROVEN,
                exposure_evidence=ev,
                exposure_confidence=0.86,
                revenue_share=0.44,
            )
        ],
        business_quality=ScoredDimension(score=82.0, evidence=ev),
        growth_durability=ScoredDimension(score=76.0, evidence=ev),
        financial_strength=ScoredDimension(score=80.0, evidence=ev),
        management=ScoredDimension(score=74.0, evidence=ev),
        catalysts=ScoredDimension(score=60.0, evidence=ev),
        valuation=Valuation(score=70.0, evidence=ev, expectations_summary="Near historical midpoint."),
    )


@pytest.fixture
def social_only_dossier() -> AssetDossier:
    """The case the tier hierarchy exists to catch: a confident forum thesis."""
    ev = [
        make_evidence(tier=SourceTier.SOCIAL, name="r/investing", age_days=2),
        make_evidence(tier=SourceTier.COMMENTARY, name="Substack post", age_days=5),
    ]
    return AssetDossier(
        symbol="SMCI",
        asset_class=AssetClass.STOCK,
        themes=[
            ThemeExposure(
                name="ai_infrastructure",
                exposure_status=ExposureStatus.PROVEN,
                exposure_evidence=ev,
                exposure_confidence=0.95,
            )
        ],
        business_quality=ScoredDimension(score=95.0, evidence=ev),
        growth_durability=ScoredDimension(score=95.0, evidence=ev),
        financial_strength=ScoredDimension(score=90.0, evidence=ev),
        valuation=Valuation(score=90.0, evidence=ev),
    )
