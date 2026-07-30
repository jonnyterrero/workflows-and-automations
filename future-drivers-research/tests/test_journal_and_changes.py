"""Persistence, point-in-time snapshots, and change detection."""
from __future__ import annotations

from fdr import scoring
from fdr.schemas import ExposureStatus, Penalties, Vote
from fdr.tools import changes, journal


class TestPersistence:
    def test_save_and_load_round_trips(self, strong_dossier):
        journal.save_dossier(scoring.finalize(strong_dossier))
        loaded = journal.load_dossier("ETN")

        assert loaded is not None
        assert loaded.symbol == "ETN"
        assert loaded.scores is not None

    def test_missing_dossier_returns_none(self):
        assert journal.load_dossier("NOTHING") is None

    def test_each_save_archives_an_immutable_snapshot(self, strong_dossier):
        """History is what makes point-in-time backtesting possible later."""
        final = scoring.finalize(strong_dossier)
        journal.save_dossier(final)
        journal.save_dossier(final)

        assert len(journal.load_snapshots("ETN")) == 2

    def test_previous_dossier_is_the_prior_snapshot(self, strong_dossier):
        first = scoring.finalize(strong_dossier)
        journal.save_dossier(first)

        strong_dossier.business_quality.score = 40.0
        journal.save_dossier(scoring.finalize(strong_dossier))

        previous = journal.load_previous_dossier("ETN")
        assert previous is not None
        assert previous.scores.quality > 40.0

    def test_no_previous_snapshot_on_first_save(self, strong_dossier):
        journal.save_dossier(scoring.finalize(strong_dossier))

        assert journal.load_previous_dossier("ETN") is None


class TestDecisionJournal:
    def test_decision_snapshots_the_evidence_available_at_the_time(self, strong_dossier):
        journal.save_dossier(scoring.finalize(strong_dossier))
        journal.record_decision(
            user_id="jonny",
            symbol="ETN",
            vote=Vote.WATCH,
            what_was_believed="Grid capex cycle has years to run.",
            risks_accepted=["Cyclical exposure to utility budgets"],
            expected_horizon_months=36,
        )
        entries = journal.list_decisions("ETN")

        assert len(entries) == 1
        assert entries[0]["dossier_snapshot"]["symbol"] == "ETN"
        assert entries[0]["supporting_evidence"]

    def test_outcome_fields_start_empty_to_prevent_look_ahead_bias(self, strong_dossier):
        journal.save_dossier(scoring.finalize(strong_dossier))
        journal.record_decision(
            user_id="jonny", symbol="ETN", vote=Vote.OWN,
            what_was_believed="Proven exposure at a fair multiple.",
        )
        entry = journal.list_decisions("ETN")[0]

        assert entry["forward_return"] is None
        assert entry["thesis_validated"] is None
        assert entry["outcome_reviewed_at"] is None

    def test_decisions_are_filtered_per_user(self, strong_dossier):
        journal.save_dossier(scoring.finalize(strong_dossier))
        journal.record_decision(
            user_id="jonny", symbol="ETN", vote=Vote.OWN, what_was_believed="a"
        )
        journal.record_decision(
            user_id="friend", symbol="ETN", vote=Vote.AVOID, what_was_believed="b"
        )

        assert len(journal.list_decisions("ETN", user_id="jonny")) == 1
        assert len(journal.list_decisions("ETN")) == 2

    def test_invalidation_conditions_default_to_the_dossier(self, strong_dossier):
        strong_dossier.what_would_invalidate = ["Backlog declines two quarters running"]
        journal.save_dossier(scoring.finalize(strong_dossier))
        journal.record_decision(
            user_id="jonny", symbol="ETN", vote=Vote.WATCH, what_was_believed="c"
        )
        entry = journal.list_decisions("ETN")[0]

        assert entry["invalidation_conditions"] == ["Backlog declines two quarters running"]

    def test_empty_journal_lists_nothing(self):
        assert journal.list_decisions("ETN") == []


class TestChangeDetection:
    def test_status_transition_is_reported(self, strong_dossier):
        before = scoring.finalize(strong_dossier)

        strong_dossier.themes[0].exposure_status = ExposureStatus.UNPROVEN
        after = scoring.finalize(strong_dossier)

        detected = changes.detect_changes(before, after)
        fields = {c.field for c in detected}

        assert "research_status" in fields

    def test_score_movement_beyond_threshold_is_reported(self, strong_dossier):
        before = scoring.finalize(strong_dossier)

        strong_dossier.business_quality.score = 40.0
        after = scoring.finalize(strong_dossier)

        detected = changes.detect_changes(before, after)
        quality = [c for c in detected if c.field == "scores.quality"]

        assert quality and quality[0].direction == "decreased"

    def test_small_movement_is_ignored(self, strong_dossier):
        before = scoring.finalize(strong_dossier)

        strong_dossier.business_quality.score = 82.5
        after = scoring.finalize(strong_dossier)

        detected = changes.detect_changes(before, after)

        assert not [c for c in detected if c.field == "scores.quality"]

    def test_rising_risk_penalty_is_reported(self, strong_dossier):
        before = scoring.finalize(strong_dossier)

        strong_dossier.penalties = Penalties(leverage=60.0)
        after = scoring.finalize(strong_dossier)

        detected = changes.detect_changes(before, after)

        assert any(c.field == "penalties.leverage" for c in detected)

    def test_theme_regrade_is_reported(self, strong_dossier):
        before = scoring.finalize(strong_dossier)

        strong_dossier.themes[0].exposure_status = ExposureStatus.PARTIAL
        after = scoring.finalize(strong_dossier)

        detected = changes.detect_changes(before, after)

        assert any(c.field.startswith("themes.") for c in detected)

    def test_invalidation_trigger_outranks_everything(self, strong_dossier):
        before = scoring.finalize(strong_dossier)
        before.what_would_invalidate = ["backlog declines sequentially for two quarters"]

        after = scoring.finalize(strong_dossier)
        after.bear_case.summary = (
            "Backlog declines began this quarter and continued sequentially "
            "for two consecutive quarters."
        )

        detected = changes.detect_changes(before, after)

        assert detected[0].invalidation_triggered is True
        assert detected[0].severity == "critical"

    def test_unmet_invalidation_condition_does_not_fire(self, strong_dossier):
        """Conservative by design: a false alarm teaches users to ignore alerts."""
        before = scoring.finalize(strong_dossier)
        before.what_would_invalidate = ["backlog declines sequentially for two quarters"]

        after = scoring.finalize(strong_dossier)
        after.bear_case.summary = "Margins compressed slightly on product mix."

        detected = changes.detect_changes(before, after)

        assert not any(c.invalidation_triggered for c in detected)

    def test_identical_dossiers_produce_no_changes(self, strong_dossier):
        final = scoring.finalize(strong_dossier)

        assert changes.detect_changes(final, final) == []

    def test_comparing_different_symbols_is_rejected(self, strong_dossier, social_only_dossier):
        import pytest

        with pytest.raises(ValueError, match="different symbols"):
            changes.detect_changes(
                scoring.finalize(strong_dossier), scoring.finalize(social_only_dossier)
            )

    def test_summary_counts_by_severity(self, strong_dossier):
        before = scoring.finalize(strong_dossier)
        strong_dossier.business_quality.score = 30.0
        after = scoring.finalize(strong_dossier)

        summary = changes.summarize_changes(changes.detect_changes(before, after))

        assert summary["total"] >= 1
        assert summary["total"] == len(summary["changes"])
