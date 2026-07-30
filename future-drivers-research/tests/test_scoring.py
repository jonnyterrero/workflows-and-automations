"""Scoring must be deterministic, gated by evidence, and never collapse to one number."""
from __future__ import annotations

import pytest

from fdr import scoring
from fdr.schemas import (
    AssetClass,
    AssetDossier,
    ExposureStatus,
    Penalties,
    PortfolioOverlap,
    ResearchStatus,
    ScoredDimension,
    SourceTier,
    ThemeExposure,
    Valuation,
)
from tests.conftest import make_evidence


class TestWeights:
    def test_default_weights_sum_to_one(self):
        scoring.DEFAULT_WEIGHTS.validate()

    def test_invalid_weights_are_rejected(self):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            scoring.Weights(business_quality=0.9).validate()


class TestExposureScoring:
    def test_proven_exposure_scores_high(self, strong_dossier):
        assert scoring.exposure_score(strong_dossier) > 80

    def test_unproven_exposure_scores_zero(self, strong_dossier):
        strong_dossier.themes[0].exposure_status = ExposureStatus.UNPROVEN

        assert scoring.exposure_score(strong_dossier) == 0.0

    def test_no_themes_scores_zero(self, strong_dossier):
        strong_dossier.themes = []

        assert scoring.exposure_score(strong_dossier) == 0.0

    def test_confidence_scales_the_score(self, strong_dossier):
        strong_dossier.themes[0].exposure_confidence = 0.5
        halved = scoring.exposure_score(strong_dossier)
        strong_dossier.themes[0].exposure_confidence = 1.0

        assert scoring.exposure_score(strong_dossier) > halved


class TestScoreDossier:
    def test_strong_candidate_scores_well_across_dimensions(self, strong_dossier):
        scores = scoring.score_dossier(strong_dossier)

        assert scores.quality > 70
        assert scores.growth > 70
        assert scores.evidence_confidence > 60
        assert 0 <= scores.composite <= 100

    def test_social_only_claims_are_capped_despite_confident_input(self, social_only_dossier):
        """The whole point: asserting 95 with a forum citation does not yield 95."""
        scores = scoring.score_dossier(social_only_dossier)

        assert scores.quality <= scoring.sources.UNCORROBORATED_SCORE_CAP
        assert scores.growth <= scoring.sources.UNCORROBORATED_SCORE_CAP
        assert scores.valuation <= scoring.sources.UNCORROBORATED_SCORE_CAP

    def test_risk_scales_the_composite_rather_than_averaging_into_it(self, strong_dossier):
        clean = scoring.score_dossier(strong_dossier)

        strong_dossier.penalties = Penalties(leverage=90.0, dilution=80.0, cyclicality=70.0)
        risky = scoring.score_dossier(strong_dossier)

        assert risky.risk < clean.risk
        assert risky.composite < clean.composite
        # Quality is untouched: a levered business can still be a good business.
        assert risky.quality == clean.quality

    def test_missing_valuation_scores_zero_not_neutral(self, strong_dossier):
        strong_dossier.valuation = None

        assert scoring.score_dossier(strong_dossier).valuation == 0.0

    def test_scoring_is_deterministic(self, strong_dossier):
        first = scoring.score_dossier(strong_dossier)
        second = scoring.score_dossier(strong_dossier)

        assert first == second


class TestPortfolioFit:
    def test_no_overlap_data_is_neutral_not_optimistic(self):
        assert scoring.portfolio_fit_score(PortfolioOverlap()) == scoring.NEUTRAL_WHEN_UNKNOWN

    def test_heavy_overlap_scores_low(self):
        fit = scoring.portfolio_fit_score(PortfolioOverlap(effective_added_weight=0.30))

        assert fit == 0.0

    def test_concentration_flags_reduce_fit(self):
        without = scoring.portfolio_fit_score(PortfolioOverlap(effective_added_weight=0.02))
        with_flags = scoring.portfolio_fit_score(
            PortfolioOverlap(
                effective_added_weight=0.02,
                concentration_flags=["semis above limit", "already held via SMH"],
            )
        )

        assert with_flags < without


class TestStatusGates:
    def test_unproven_exposure_gates_before_anything_else(self, strong_dossier):
        """Even a cheap, high-quality company is stopped by unproven exposure."""
        strong_dossier.themes[0].exposure_status = ExposureStatus.UNPROVEN
        final = scoring.finalize(strong_dossier)

        assert final.research_status is ResearchStatus.EXPOSURE_NOT_PROVEN

    def test_severe_risk_gates_before_valuation(self, strong_dossier):
        strong_dossier.penalties = Penalties(
            leverage=95.0, dilution=95.0, cyclicality=95.0,
            customer_concentration=95.0, regulatory=95.0, geographic=95.0,
            crowded_expectations=95.0,
        )
        final = scoring.finalize(strong_dossier)

        assert final.research_status is ResearchStatus.RISK_EXCEEDS_REWARD

    def test_expensive_but_high_quality_is_valuation_gated(self, strong_dossier):
        strong_dossier.valuation = Valuation(
            score=15.0,
            evidence=[make_evidence(tier=SourceTier.LICENSED, name="Market data vendor")],
            expectations_summary="88th percentile of its own five-year range.",
        )
        final = scoring.finalize(strong_dossier)

        assert final.research_status is ResearchStatus.VALUATION_GATED

    def test_overlap_concern_is_surfaced(self, strong_dossier):
        strong_dossier.portfolio_overlap = PortfolioOverlap(
            effective_added_weight=0.24,
            concentration_flags=["semis 41% post-trade", "held via SMH", "held via QQQM"],
        )
        final = scoring.finalize(strong_dossier)

        assert final.research_status is ResearchStatus.PORTFOLIO_OVERLAP_CONCERN

    def test_strong_candidate_advances(self, strong_dossier):
        final = scoring.finalize(strong_dossier)

        assert final.research_status is ResearchStatus.ADVANCE_TO_DEEPER_RESEARCH

    def test_no_status_is_a_buy_or_sell_recommendation(self):
        values = {status.value for status in ResearchStatus}
        forbidden = {"buy", "sell", "strong_buy", "hold", "overweight"}

        assert not (values & forbidden)


class TestFinalize:
    def test_finalize_attaches_scores_and_does_not_mutate_input(self, strong_dossier):
        assert strong_dossier.scores is None
        final = scoring.finalize(strong_dossier)

        assert final.scores is not None
        assert strong_dossier.scores is None

    def test_tier_five_evidence_is_routed_to_the_narrative_panel(self, social_only_dossier):
        """Social material stays visible as context, having never touched the score."""
        final = scoring.finalize(social_only_dossier)

        tiers = {e.source_tier for e in final.narrative_panel.evidence}
        assert SourceTier.SOCIAL in tiers

    def test_computed_penalties_reflect_source_quality(self, social_only_dossier):
        final = scoring.finalize(social_only_dossier)

        assert final.penalties.source_weakness > 50

    def test_explain_reports_dimensions_not_a_single_number(self, strong_dossier):
        final = scoring.finalize(strong_dossier)
        summary = scoring.explain(final.scores)

        for dimension in ("quality", "growth", "valuation", "risk"):
            assert dimension in summary


class TestUnknownIsNotZero:
    def test_undisclosed_theme_share_does_not_zero_the_score(self, strong_dossier):
        """A company that does not size its exposure is not scored as having none."""
        strong_dossier.themes[0].revenue_share = None
        dossier = AssetDossier.model_validate(strong_dossier.model_dump())

        assert scoring.exposure_score(dossier) > 0

    def test_empty_dossier_scores_zero_rather_than_erroring(self):
        bare = AssetDossier(symbol="TEST", asset_class=AssetClass.STOCK)
        scores = scoring.score_dossier(bare)

        assert scores.composite == 0.0
        assert scores.evidence_confidence == 0.0


class TestThemeSelection:
    def test_best_theme_wins_when_several_are_tracked(self, strong_dossier):
        strong_dossier.themes.append(
            ThemeExposure(
                name="speculative_theme",
                exposure_status=ExposureStatus.UNPROVEN,
                exposure_evidence=[make_evidence(tier=SourceTier.SOCIAL)],
                exposure_confidence=0.9,
            )
        )
        # The weak second theme must not drag down the proven first one.
        assert scoring.exposure_score(strong_dossier) > 80

    def test_dimension_with_no_evidence_scores_zero(self, strong_dossier):
        strong_dossier.business_quality = ScoredDimension(score=90.0, evidence=[])

        assert scoring.score_dossier(strong_dossier).quality == 0.0
