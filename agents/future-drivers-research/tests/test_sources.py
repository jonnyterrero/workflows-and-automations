"""The tier hierarchy is the platform's central claim. These tests defend it."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from fdr import sources
from fdr.schemas import SourceTier
from tests.conftest import make_evidence


class TestScoreGating:
    def test_social_only_evidence_is_capped(self):
        """A confident forum thesis cannot buy its way to a high score."""
        evidence = [make_evidence(tier=SourceTier.SOCIAL, name="r/investing")]
        result = sources.gate_score(95.0, evidence)

        assert result.capped is True
        assert result.score == sources.UNCORROBORATED_SCORE_CAP
        assert "Tier 5" in result.reason

    def test_commentary_only_evidence_is_capped(self):
        evidence = [make_evidence(tier=SourceTier.COMMENTARY, name="Analyst blog")]
        assert sources.gate_score(88.0, evidence).capped is True

    def test_filing_evidence_passes_through_uncapped(self):
        evidence = [make_evidence(tier=SourceTier.REGULATORY)]
        result = sources.gate_score(95.0, evidence)

        assert result.capped is False
        assert result.score == 95.0

    def test_one_authoritative_source_lifts_the_cap(self):
        """Tier 5 may trigger investigation; Tier 1 corroboration unlocks scoring."""
        evidence = [
            make_evidence(tier=SourceTier.SOCIAL, name="r/investing"),
            make_evidence(tier=SourceTier.REGULATORY, name="SEC 10-K"),
        ]
        result = sources.gate_score(90.0, evidence)

        assert result.capped is False
        assert result.score == 90.0

    def test_low_score_below_cap_is_not_altered(self):
        evidence = [make_evidence(tier=SourceTier.SOCIAL)]
        result = sources.gate_score(20.0, evidence)

        assert result.capped is False
        assert result.score == 20.0

    def test_no_evidence_scores_zero(self):
        result = sources.gate_score(99.0, [])

        assert result.capped is True
        assert result.score == 0.0


class TestEvidenceConfidence:
    def test_no_evidence_is_zero_confidence(self):
        assert sources.evidence_confidence([]) == 0.0

    def test_filings_beat_forums(self):
        filing = sources.evidence_confidence([make_evidence(tier=SourceTier.REGULATORY)])
        forum = sources.evidence_confidence([make_evidence(tier=SourceTier.SOCIAL)])

        assert filing > forum

    def test_breadth_increases_confidence(self):
        one = sources.evidence_confidence([make_evidence(name="SEC 10-K")])
        three = sources.evidence_confidence(
            [
                make_evidence(name="SEC 10-K"),
                make_evidence(name="SEC 10-Q"),
                make_evidence(name="Issuer holdings file"),
            ]
        )

        assert three > one

    def test_repeated_reads_of_one_document_do_not_count_as_breadth(self):
        """Deduplicated by source name, so one filing read five ways is one source."""
        once = sources.evidence_confidence([make_evidence(name="SEC 10-K")])
        five_times = sources.evidence_confidence([make_evidence(name="SEC 10-K") for _ in range(5)])

        assert five_times == pytest.approx(once)

    def test_stale_evidence_lowers_confidence(self):
        fresh = sources.evidence_confidence([make_evidence(age_days=10)])
        old = sources.evidence_confidence([make_evidence(age_days=900)])

        assert fresh > old


class TestFreshness:
    def test_recent_evidence_is_fully_fresh(self):
        assert sources.freshness_factor(make_evidence(age_days=10)) == 1.0

    def test_very_old_evidence_decays_to_zero(self):
        assert sources.freshness_factor(make_evidence(age_days=800)) == 0.0

    def test_undated_evidence_gets_a_neutral_factor(self):
        evidence = make_evidence()
        evidence.published_at = None

        assert sources.freshness_factor(evidence) == sources.UNKNOWN_DATE_FRESHNESS

    def test_naive_datetimes_are_treated_as_utc(self):
        """Guards a crash on tz-naive input rather than silently mis-ageing it."""
        evidence = make_evidence()
        evidence.published_at = datetime.now() - timedelta(days=5)

        assert sources.freshness_factor(evidence) == 1.0


class TestPartitioning:
    def test_splits_authoritative_from_hypothesis(self):
        evidence = [
            make_evidence(tier=SourceTier.REGULATORY),
            make_evidence(tier=SourceTier.JOURNALISM),
            make_evidence(tier=SourceTier.SOCIAL),
            make_evidence(tier=SourceTier.COMMENTARY),
        ]
        authoritative, hypothesis = sources.partition_by_authority(evidence)

        assert len(authoritative) == 2
        assert len(hypothesis) == 2

    def test_best_tier_picks_most_authoritative(self):
        evidence = [
            make_evidence(tier=SourceTier.SOCIAL),
            make_evidence(tier=SourceTier.LICENSED),
        ]

        assert sources.best_tier(evidence) is SourceTier.LICENSED

    def test_best_tier_of_nothing_is_none(self):
        assert sources.best_tier([]) is None


class TestPenalties:
    def test_weak_sources_penalised_more_than_filings(self):
        weak = sources.source_weakness_penalty([make_evidence(tier=SourceTier.SOCIAL)])
        strong = sources.source_weakness_penalty([make_evidence(tier=SourceTier.REGULATORY)])

        assert weak > strong
        assert strong == pytest.approx(0.0)

    def test_absent_evidence_is_maximally_penalised(self):
        assert sources.staleness_penalty([]) == 100.0
        assert sources.source_weakness_penalty([]) == 100.0
