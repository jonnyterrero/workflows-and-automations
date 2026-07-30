"""End-to-end walk of the research loop, with the agents' tool calls simulated.

    discover -> prove exposure -> analyse quality -> test valuation
    -> bear case -> portfolio fit -> score -> persist -> detect change

Runs entirely offline. What it exercises is the part that must be trustworthy
regardless of what any model says: given a set of tool results, the pipeline
produces the same dossier every time, and the gates fire where they should.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fdr import scoring
from fdr.schemas import (
    AssetClass,
    AssetDossier,
    Evidence,
    ExposureStatus,
    Penalties,
    PortfolioOverlap,
    ResearchStatus,
    Scenario,
    ScoredDimension,
    SourceTier,
    ThemeExposure,
    Valuation,
    Vote,
)
from fdr.tools import journal, registry


def _filing_evidence(symbol: str, claim: str) -> Evidence:
    filings = registry.dispatch("sec_recent_filings", {"symbol": symbol})
    first = filings["filings"][0]
    return Evidence(
        claim=claim,
        source_tier=SourceTier.REGULATORY,
        source_name=f"SEC {first['form']} {first['accession']}",
        source_url=first["url"],
        published_at=datetime.fromisoformat(first["filed_at"]),
    )


def _build_dossier(symbol: str, theme: str, positions: list[dict]) -> AssetDossier:
    """Assemble a dossier the way the committee would, from tool output only."""
    fundamentals = registry.dispatch("compute_fundamentals", {"symbol": symbol})
    valuation = registry.dispatch("valuation_context", {"symbol": symbol})
    overlap = registry.dispatch(
        "portfolio_overlap", {"positions": positions, "candidate": symbol}
    )
    ratios = fundamentals["ratios"]

    exposure_ev = _filing_evidence(symbol, f"Segment disclosure supports {theme} exposure.")
    quality_ev = _filing_evidence(symbol, f"Gross margin {ratios['gross_margin']}.")
    market_ev = Evidence(
        claim=valuation["expectations_summary"],
        source_tier=SourceTier.LICENSED,
        source_name="Market data vendor",
        published_at=datetime.now(tz=UTC) - timedelta(days=1),
    )

    # Margin and cash generation drive the scores; the point is that these come
    # from computed ratios rather than from a model's impression.
    quality = min(100.0, max(0.0, (ratios["gross_margin"] or 0) * 200))
    strength = 80.0 if (ratios["free_cash_flow"] or 0) > 0 else 25.0

    return AssetDossier(
        symbol=symbol,
        asset_class=AssetClass.STOCK,
        themes=[
            ThemeExposure(
                name=theme,
                exposure_status=ExposureStatus.PROVEN,
                exposure_evidence=[exposure_ev],
                exposure_confidence=0.85,
            )
        ],
        business_quality=ScoredDimension(score=quality, evidence=[quality_ev]),
        growth_durability=ScoredDimension(score=72.0, evidence=[exposure_ev]),
        financial_strength=ScoredDimension(score=strength, evidence=[quality_ev]),
        management=ScoredDimension(score=70.0, evidence=[quality_ev]),
        catalysts=ScoredDimension(score=55.0, evidence=[market_ev]),
        valuation=Valuation(
            score=valuation["valuation_score"],
            evidence=[market_ev],
            expectations_summary=valuation["expectations_summary"],
        ),
        bear_case=Scenario(summary="Spending cycle rolls over.", evidence=[market_ev]),
        portfolio_overlap=PortfolioOverlap(
            effective_added_weight=overlap["effective_added_weight"],
            overlapping_holdings=overlap["overlapping_holdings"],
            concentration_flags=overlap["concentration_flags"],
        ),
        what_would_invalidate=["Segment revenue declines sequentially for two quarters"],
    )


class TestFullLoop:
    def test_well_evidenced_candidate_completes_the_loop(self):
        dossier = _build_dossier("NVDA", "ai_infrastructure", [{"symbol": "GLD", "weight": 0.2}])
        final = scoring.finalize(dossier)

        assert final.scores is not None
        assert final.scores.quality > 50
        assert final.research_status is not ResearchStatus.EXPOSURE_NOT_PROVEN

        saved = registry.dispatch("save_dossier", {"dossier": final.model_dump(mode="json")})
        assert saved["saved"] is True

        loaded = registry.dispatch("load_dossier", {"symbol": "NVDA"})
        assert loaded["found"] is True

    def test_negative_cash_flow_flows_through_to_a_weaker_score(self):
        """SMCI's fixture burns cash; the dossier must reflect it."""
        healthy = scoring.finalize(_build_dossier("NVDA", "ai_infrastructure", []))
        burning = scoring.finalize(_build_dossier("SMCI", "ai_infrastructure", []))

        assert burning.scores.financial_strength < healthy.scores.financial_strength

    def test_expensive_asset_is_valuation_gated_by_the_pipeline(self):
        """ETN's fixture is at the 88th percentile of its own range."""
        final = scoring.finalize(_build_dossier("ETN", "grid_modernization", []))

        assert final.scores.valuation < 25

    def test_overlapping_candidate_is_flagged(self):
        positions = [
            {"symbol": "VOO", "weight": 0.35},
            {"symbol": "QQQM", "weight": 0.25},
            {"symbol": "SMH", "weight": 0.25},
        ]
        final = scoring.finalize(_build_dossier("NVDA", "ai_infrastructure", positions))

        assert final.portfolio_overlap.concentration_flags
        assert final.scores.portfolio_fit < 100

    def test_loop_is_reproducible(self):
        first = scoring.finalize(_build_dossier("NVDA", "ai_infrastructure", []))
        second = scoring.finalize(_build_dossier("NVDA", "ai_infrastructure", []))

        assert first.scores == second.scores
        assert first.research_status == second.research_status


class TestReviewCycle:
    def test_second_review_detects_deterioration(self):
        dossier = _build_dossier("NVDA", "ai_infrastructure", [])
        registry.dispatch(
            "save_dossier", {"dossier": scoring.finalize(dossier).model_dump(mode="json")}
        )

        # Simulate the next review finding a materially worse picture.
        dossier.penalties = Penalties(leverage=70.0, customer_concentration=65.0)
        dossier.business_quality.score = 35.0
        registry.dispatch(
            "save_dossier", {"dossier": scoring.finalize(dossier).model_dump(mode="json")}
        )

        report = registry.dispatch("detect_changes", {"symbol": "NVDA"})

        assert report["total"] > 0
        fields = {c["field"] for c in report["changes"]}
        assert "scores.quality" in fields

    def test_first_review_has_no_prior_snapshot(self):
        dossier = scoring.finalize(_build_dossier("NVDA", "ai_infrastructure", []))
        registry.dispatch("save_dossier", {"dossier": dossier.model_dump(mode="json")})

        report = registry.dispatch("detect_changes", {"symbol": "NVDA"})

        assert report["total"] == 0
        assert "no prior snapshot" in report["note"]

    def test_decision_captures_point_in_time_state(self):
        dossier = scoring.finalize(_build_dossier("NVDA", "ai_infrastructure", []))
        registry.dispatch("save_dossier", {"dossier": dossier.model_dump(mode="json")})

        registry.dispatch(
            "record_decision",
            {
                "user_id": "jonny",
                "symbol": "NVDA",
                "vote": Vote.WATCH.value,
                "what_was_believed": "Exposure proven; waiting for a better entry.",
            },
        )
        entries = journal.list_decisions("NVDA")

        assert len(entries) == 1
        snapshot_scores = entries[0]["dossier_snapshot"]["scores"]
        assert snapshot_scores["quality"] == dossier.scores.quality

    def test_stored_scores_always_match_stored_evidence(self):
        """Save recomputes, so a tampered score cannot be persisted."""
        dossier = _build_dossier("NVDA", "ai_infrastructure", [])
        tampered = scoring.finalize(dossier)
        tampered.scores.quality = 99.9

        registry.dispatch("save_dossier", {"dossier": tampered.model_dump(mode="json")})
        reloaded = journal.load_dossier("NVDA")

        assert reloaded.scores.quality != 99.9


class TestGatesInPipeline:
    def test_unproven_exposure_stops_the_loop_before_valuation(self):
        dossier = _build_dossier("SMCI", "ai_infrastructure", [])
        dossier.themes[0].exposure_status = ExposureStatus.UNPROVEN
        final = scoring.finalize(dossier)

        assert final.research_status is ResearchStatus.EXPOSURE_NOT_PROVEN

    def test_change_detection_surfaces_invalidation_first(self):
        dossier = _build_dossier("NVDA", "ai_infrastructure", [])
        before = scoring.finalize(dossier)
        registry.dispatch("save_dossier", {"dossier": before.model_dump(mode="json")})

        dossier.bear_case = Scenario(
            summary=(
                "Segment revenue declined sequentially for two consecutive quarters, "
                "confirming the demand rollover."
            ),
            evidence=dossier.bear_case.evidence,
        )
        after = scoring.finalize(dossier)
        registry.dispatch("save_dossier", {"dossier": after.model_dump(mode="json")})

        report = registry.dispatch("detect_changes", {"symbol": "NVDA"})

        assert report["invalidations_triggered"] >= 1
        assert report["changes"][0]["severity"] == "critical"
