"""Unit tests for the pure portfolio policy engine."""
from __future__ import annotations

from packages.policy.defaults import DEFAULT_POLICY_RULES, DEFAULT_PORTFOLIO_POSITIONS, DEFAULT_PROFILE
from packages.policy.evaluator import evaluate_portfolio_decision
from packages.policy.models import (
    AssetCandidate,
    MacroRegime,
    PolicyDecision,
    PortfolioAssetClass,
    PortfolioDecisionInput,
    PortfolioPosition,
    PortfolioRiskLevel,
    PortfolioSignalDirection,
    SignalOutput,
)


def _base_input(
    asset: AssetCandidate,
    proposed_weight: float,
    *,
    positions: list[PortfolioPosition] | None = None,
    risk_sentiment: str = "risk_on",
    growth_regime: str = "expansion",
    data_is_stale: bool = False,
    above_sma200: bool | None = True,
) -> PortfolioDecisionInput:
    return PortfolioDecisionInput(
        profile=DEFAULT_PROFILE.model_copy(deep=True),
        current_positions=[position.model_copy(deep=True) for position in (positions or DEFAULT_PORTFOLIO_POSITIONS)],
        proposed_asset=asset,
        proposed_weight=proposed_weight,
        macro_regime=MacroRegime(
            growth_regime=growth_regime,
            inflation_regime="disinflationary",
            rate_regime="moderately_restrictive",
            liquidity_regime="neutral",
            risk_sentiment=risk_sentiment,
            stale_data=data_is_stale,
        ),
        model_signal=SignalOutput(
            symbol=asset.symbol,
            signal=PortfolioSignalDirection.POSITIVE,
            confidence=0.67,
            expected_return_bucket="outperform",
        ),
        policy_rules=[rule.model_copy(deep=True) for rule in DEFAULT_POLICY_RULES],
        data_is_stale=data_is_stale,
        above_sma200=above_sma200,
    )


def test_allowed_voo_addition() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="VOO",
                name="Vanguard S&P 500 ETF",
                asset_class=PortfolioAssetClass.ETF,
                theme_tags=["core_equity", "us_broad_equity"],
            ),
            0.35,
        )
    )
    assert result.decision == PolicyDecision.ALLOW
    assert result.allowed is True


def test_blocked_crypto_overweight_above_8_percent() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="BTC",
                name="Bitcoin",
                asset_class=PortfolioAssetClass.CRYPTO,
                theme_tags=["crypto"],
            ),
            0.09,
        )
    )
    assert result.decision == PolicyDecision.BLOCK
    assert any("Crypto exposure" in violation for violation in result.violations)


def test_warn_ai_semis_near_15_percent_cap() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="SMH",
                name="VanEck Semiconductor ETF",
                asset_class=PortfolioAssetClass.ETF,
                theme_tags=["ai_semis", "thematic_tech"],
            ),
            0.14,
        )
    )
    assert result.decision == PolicyDecision.WARN
    assert any("AI/semiconductors exposure is near" in warning for warning in result.warnings)


def test_block_single_stock_above_5_percent() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="NVDA",
                name="NVIDIA Corporation",
                asset_class=PortfolioAssetClass.EQUITY,
                theme_tags=["ai_semis", "thematic_tech"],
            ),
            0.06,
        )
    )
    assert result.decision == PolicyDecision.BLOCK
    assert any("Single-name exposure exceeds" in violation for violation in result.violations)


def test_warn_uranium_near_8_percent_cap() -> None:
    positions = [position.model_copy(deep=True) for position in DEFAULT_PORTFOLIO_POSITIONS]
    positions = [position for position in positions if position.symbol != "NLR"]
    positions.append(
        PortfolioPosition(
            symbol="URA",
            asset_class=PortfolioAssetClass.ETF,
            portfolio_weight=0.07,
            theme_tags=["energy_power_nuclear", "nuclear_uranium"],
        )
    )
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="URA",
                name="Global X Uranium ETF",
                asset_class=PortfolioAssetClass.ETF,
                theme_tags=["energy_power_nuclear", "nuclear_uranium"],
            ),
            0.07,
            positions=positions,
        )
    )
    assert result.decision == PolicyDecision.WARN
    assert any("Nuclear/uranium exposure is near" in warning for warning in result.warnings)


def test_block_if_bonds_cash_below_10_percent() -> None:
    positions = [
        position.model_copy(update={"portfolio_weight": 0.03})
        if position.symbol in {"BND", "SGOV"}
        else position.model_copy(deep=True)
        for position in DEFAULT_PORTFOLIO_POSITIONS
    ]
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="SMH",
                name="VanEck Semiconductor ETF",
                asset_class=PortfolioAssetClass.ETF,
                theme_tags=["ai_semis", "thematic_tech"],
            ),
            0.08,
            positions=positions,
        )
    )
    assert result.decision == PolicyDecision.BLOCK
    assert any("Bonds/cash would fall" in violation for violation in result.violations)


def test_allow_gold_up_to_5_percent() -> None:
    positions = [position.model_copy(deep=True) for position in DEFAULT_PORTFOLIO_POSITIONS if position.symbol not in {"GLD", "SLV"}]
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="GLD",
                name="SPDR Gold Shares",
                asset_class=PortfolioAssetClass.METAL,
                theme_tags=["precious_metals", "gold"],
            ),
            0.05,
            positions=positions,
        )
    )
    assert result.decision == PolicyDecision.ALLOW


def test_warn_metals_above_5_percent() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="GLD",
                name="SPDR Gold Shares",
                asset_class=PortfolioAssetClass.METAL,
                theme_tags=["precious_metals", "gold"],
            ),
            0.06,
        )
    )
    assert result.decision == PolicyDecision.WARN
    assert any("Precious metals exposure would move above" in warning for warning in result.warnings)


def test_block_metals_above_10_percent() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="GLD",
                name="SPDR Gold Shares",
                asset_class=PortfolioAssetClass.METAL,
                theme_tags=["precious_metals", "gold"],
            ),
            0.11,
        )
    )
    assert result.decision == PolicyDecision.BLOCK
    assert any("Precious metals exposure would rise" in violation for violation in result.violations)


def test_block_speculative_single_name_above_1_point_5_percent() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="OKLO",
                name="Oklo",
                asset_class=PortfolioAssetClass.EQUITY,
                theme_tags=["energy_power_nuclear", "nuclear_uranium"],
                is_speculative=True,
            ),
            0.02,
        )
    )
    assert result.decision == PolicyDecision.BLOCK
    assert any("Speculative single-name exposure exceeds" in violation for violation in result.violations)


def test_downgrade_risk_in_recession_risk_off_regime() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="SMH",
                name="VanEck Semiconductor ETF",
                asset_class=PortfolioAssetClass.ETF,
                theme_tags=["ai_semis", "thematic_tech"],
            ),
            0.08,
            risk_sentiment="risk_off",
            growth_regime="recession",
        )
    )
    assert result.riskLevel in {PortfolioRiskLevel.MODERATE, PortfolioRiskLevel.ELEVATED, PortfolioRiskLevel.SEVERE}
    assert any("risk-off" in warning.lower() for warning in result.warnings)


def test_downgrade_crypto_during_risk_off_regime() -> None:
    positions = [position.model_copy(deep=True) for position in DEFAULT_PORTFOLIO_POSITIONS if "crypto" not in position.theme_tags]
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="BTC",
                name="Bitcoin",
                asset_class=PortfolioAssetClass.CRYPTO,
                theme_tags=["crypto"],
            ),
            0.05,
            positions=positions,
            risk_sentiment="risk_off",
            growth_regime="recession",
        )
    )
    assert result.decision == PolicyDecision.WARN
    assert any("Crypto exposure is being proposed during a risk-off regime" in warning for warning in result.warnings)


def test_warn_when_data_is_stale() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="VOO",
                name="Vanguard S&P 500 ETF",
                asset_class=PortfolioAssetClass.ETF,
                theme_tags=["core_equity", "us_broad_equity"],
            ),
            0.35,
            data_is_stale=True,
        )
    )
    assert result.decision == PolicyDecision.WARN
    assert any("Data freshness is stale" in warning for warning in result.warnings)


def test_warn_when_asset_is_below_sma200_despite_positive_signal() -> None:
    result = evaluate_portfolio_decision(
        _base_input(
            AssetCandidate(
                symbol="SMH",
                name="VanEck Semiconductor ETF",
                asset_class=PortfolioAssetClass.ETF,
                theme_tags=["ai_semis", "thematic_tech"],
            ),
            0.08,
            above_sma200=False,
        )
    )
    assert result.decision == PolicyDecision.WARN
    assert any("below SMA200" in warning for warning in result.warnings)
