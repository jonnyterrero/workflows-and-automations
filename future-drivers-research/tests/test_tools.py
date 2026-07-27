"""Host-side tool behaviour, exercised offline against fixtures."""
from __future__ import annotations

import pytest

from fdr.tools import filings, macro, market, portfolio, registry


class TestFilings:
    def test_company_facts_returns_tier_one(self):
        result = filings.sec_company_facts("NVDA")

        assert result["source_tier"] == 1
        assert result["facts"]["revenue"]["value"] > 0

    def test_recent_filings_are_tier_one(self):
        result = filings.sec_recent_filings("NVDA")

        assert result["source_tier"] == 1
        assert result["filings"]

    def test_form_filter_is_applied(self):
        result = filings.sec_recent_filings("ETN", forms=["10-Q"])

        assert all(f["form"] == "10-Q" for f in result["filings"])

    def test_unknown_symbol_reports_an_error_rather_than_guessing(self):
        assert "error" in filings.sec_company_facts("NOTATICKER")


class TestFundamentals:
    def test_ratios_are_computed_from_reported_values(self):
        facts = filings.sec_company_facts("NVDA")["facts"]
        ratios = market.compute_fundamentals(facts)

        assert 0 < ratios["gross_margin"] < 1
        assert ratios["free_cash_flow"] > 0

    def test_negative_cash_flow_is_preserved(self):
        """SMCI's fixture has negative operating cash flow; it must not be hidden."""
        facts = filings.sec_company_facts("SMCI")["facts"]
        ratios = market.compute_fundamentals(facts)

        assert ratios["free_cash_flow"] < 0

    def test_missing_inputs_yield_none_not_zero(self):
        ratios = market.compute_fundamentals({"revenue": {"value": 100.0}})

        assert ratios["gross_margin"] is None
        assert "gross_profit" not in ratios["inputs_present"]

    def test_division_by_zero_is_survived(self):
        ratios = market.compute_fundamentals(
            {"revenue": {"value": 0.0}, "gross_profit": {"value": 50.0}}
        )

        assert ratios["gross_margin"] is None

    def test_missing_inputs_are_reported(self):
        facts = filings.sec_company_facts("ETN")["facts"]
        ratios = market.compute_fundamentals(facts)

        assert isinstance(ratios["inputs_missing"], list)


class TestValuation:
    def test_expensive_asset_scores_low(self):
        """ETN's fixture sits at the 88th/93rd percentile of its own range."""
        result = market.valuation_context("ETN")

        assert result["valuation_score"] < 25
        assert result["signals"]

    def test_cheaper_asset_scores_higher(self):
        expensive = market.valuation_context("ETN")["valuation_score"]
        cheaper = market.valuation_context("SMCI")["valuation_score"]

        assert cheaper > expensive

    def test_percentile_language_is_surfaced(self):
        result = market.valuation_context("ETN")

        assert "percentile" in result["expectations_summary"].lower()

    def test_unknown_symbol_errors_cleanly(self):
        assert "error" in market.valuation_context("NOTATICKER")


class TestMacro:
    def test_series_returns_tier_one_with_trend(self):
        result = macro.fred_series("IPUTIL")

        assert result["source_tier"] == 1
        assert result["direction"] in {"rising", "falling", "flat"}

    def test_rising_series_is_labelled_rising(self):
        assert macro.fred_series("IPUTIL")["direction"] == "rising"

    def test_unknown_series_lists_alternatives(self):
        result = macro.fred_series("NOTASERIES")

        assert "error" in result


class TestPortfolioOverlap:
    def test_hidden_semiconductor_concentration_is_detected(self):
        """The brief's example: VOO + QQQM + SMH + NVDA is one bet, not four."""
        positions = [
            {"symbol": "VOO", "weight": 0.40},
            {"symbol": "QQQM", "weight": 0.25},
            {"symbol": "SMH", "weight": 0.20},
        ]
        result = portfolio.portfolio_overlap(positions, "NVDA", candidate_weight=0.10)

        assert result["already_held_indirectly"] > 0.05
        assert result["concentration_flags"]
        assert result["factor_exposures_after"]["semiconductors"] > 0.25

    def test_crypto_exposure_aggregates_across_differently_named_holdings(self):
        """IBIT + COIN + MSTR is a single underlying risk."""
        positions = [
            {"symbol": "IBIT", "weight": 0.10},
            {"symbol": "COIN", "weight": 0.05},
        ]
        result = portfolio.portfolio_overlap(positions, "MSTR", candidate_weight=0.05)

        assert result["factor_exposures_after"]["crypto_beta"] > 0.15

    def test_unrelated_candidate_adds_genuinely_new_exposure(self):
        positions = [{"symbol": "GLD", "weight": 0.10}]
        result = portfolio.portfolio_overlap(positions, "ETN", candidate_weight=0.05)

        assert result["already_held_indirectly"] == 0.0
        assert result["effective_added_weight"] == pytest.approx(0.05)

    def test_look_through_conserves_total_weight(self):
        positions = [{"symbol": "VOO", "weight": 0.5}, {"symbol": "SMH", "weight": 0.5}]
        effective = portfolio.look_through(positions)

        assert sum(effective.values()) == pytest.approx(1.0, abs=1e-6)

    def test_unknown_ticker_passes_through_undecomposed(self):
        effective = portfolio.look_through([{"symbol": "PRIVATECO", "weight": 0.3}])

        assert effective["PRIVATECO"] == pytest.approx(0.3)


class TestRegistryDispatch:
    def test_dispatch_routes_to_the_handler(self):
        result = registry.dispatch("compute_fundamentals", {"symbol": "NVDA"})

        assert result["symbol"] == "NVDA"
        assert result["ratios"]["gross_margin"] is not None

    def test_unknown_tool_returns_an_error_not_an_exception(self):
        result = registry.dispatch("no_such_tool", {})

        assert "error" in result
        assert "available" in result

    def test_handler_exceptions_are_returned_as_tool_errors(self):
        """A crash in our process must not stall the agent session."""
        result = registry.dispatch("compute_fundamentals", {})

        assert "error" in result
        assert result["tool"] == "compute_fundamentals"

    def test_score_dossier_recomputes_rather_than_trusting_input(self, social_only_dossier):
        payload = social_only_dossier.model_dump(mode="json")
        result = registry.dispatch("score_dossier", {"dossier": payload})

        # Input claimed 95s on forum sourcing; the gate caps them.
        assert result["scores"]["quality"] <= 45.0

    def test_every_spec_has_a_callable_handler(self):
        for spec in registry.TOOL_SPECS:
            assert callable(spec.handler), spec.name

    def test_tool_names_are_unique(self):
        names = [spec.name for spec in registry.TOOL_SPECS]

        assert len(names) == len(set(names))
