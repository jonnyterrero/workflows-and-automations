"""Pure portfolio policy and risk evaluation logic."""
from __future__ import annotations

from dataclasses import dataclass

from packages.policy.models import (
    PolicyDecision,
    PolicyRule,
    PortfolioAssetClass,
    PortfolioDecisionInput,
    PortfolioPosition,
    PortfolioRiskLevel,
    PortfolioSignalDirection,
    RiskEvaluationResult,
)

THEMATIC_TAGS = {"thematic_tech", "ai_semis", "cloud_saas", "cybersecurity", "energy_power_nuclear"}


@dataclass
class _ExposureSummary:
    core_equity: float
    thematic: float
    ai_semis: float
    nuclear_uranium: float
    precious_metals: float
    crypto: float
    bonds_cash: float
    portfolio_total: float


def _find_rule(rules: list[PolicyRule], rule_name: str) -> PolicyRule | None:
    for rule in rules:
        if rule.rule_name == rule_name and rule.is_active:
            return rule
    return None


def _theme_weight(positions: list[PortfolioPosition], theme_tag: str) -> float:
    return sum(position.portfolio_weight for position in positions if theme_tag in position.theme_tags)


def _thematic_weight(positions: list[PortfolioPosition]) -> float:
    total = 0.0
    for position in positions:
        if any(tag in THEMATIC_TAGS for tag in position.theme_tags):
            total += position.portfolio_weight
    return total


def _positions_after_proposal(
    positions: list[PortfolioPosition],
    proposed_symbol: str,
    proposed_position: PortfolioPosition,
) -> list[PortfolioPosition]:
    replaced = False
    updated: list[PortfolioPosition] = []
    for position in positions:
        if position.symbol == proposed_symbol:
            updated.append(proposed_position)
            replaced = True
        else:
            updated.append(position)
    if not replaced:
        updated.append(proposed_position)
    return updated


def _summarize_exposures(positions: list[PortfolioPosition]) -> _ExposureSummary:
    core_equity_weight = sum(
        position.portfolio_weight
        for position in positions
        if "core_equity" in position.theme_tags or "growth_tilt" in position.theme_tags
    )
    return _ExposureSummary(
        core_equity=core_equity_weight,
        thematic=_thematic_weight(positions),
        ai_semis=_theme_weight(positions, "ai_semis"),
        nuclear_uranium=_theme_weight(positions, "nuclear_uranium"),
        precious_metals=_theme_weight(positions, "precious_metals"),
        crypto=_theme_weight(positions, "crypto"),
        bonds_cash=_theme_weight(positions, "bonds_cash"),
        portfolio_total=sum(position.portfolio_weight for position in positions),
    )


def _positive_signal(input_data: PortfolioDecisionInput) -> bool:
    signal = input_data.model_signal
    if signal is None:
        return False
    return signal.signal in {
        PortfolioSignalDirection.POSITIVE,
        PortfolioSignalDirection.STRONG_POSITIVE,
    }


def _risk_level(violations: list[str], warnings: list[str], proposed: PortfolioPosition, risk_off: bool) -> PortfolioRiskLevel:
    if violations:
        return PortfolioRiskLevel.SEVERE
    score = len(warnings)
    if risk_off:
        score += 1
    if proposed.asset_class == PortfolioAssetClass.CRYPTO or proposed.is_speculative:
        score += 1
    if score >= 4:
        return PortfolioRiskLevel.ELEVATED
    if score >= 2:
        return PortfolioRiskLevel.MODERATE
    return PortfolioRiskLevel.LOW


def _adjusted_recommendation(
    decision: PolicyDecision,
    warnings: list[str],
    violations: list[str],
    proposed: PortfolioPosition,
    positive_signal: bool,
) -> str:
    if decision == PolicyDecision.BLOCK:
        if any("bonds/cash" in item or "core broad equity" in item for item in violations):
            return "rebalance before adding"
        return "avoid / wait"
    if decision == PolicyDecision.WARN:
        if proposed.asset_class == PortfolioAssetClass.CRYPTO or proposed.is_speculative:
            return "speculative only"
        if any("near" in item.lower() for item in warnings):
            return "watchlist"
        return "accumulation candidate"
    if positive_signal:
        return "accumulation candidate"
    return "watchlist"


def evaluate_portfolio_decision(input_data: PortfolioDecisionInput) -> RiskEvaluationResult:
    proposed_position = PortfolioPosition(
        symbol=input_data.proposed_asset.symbol,
        asset_class=input_data.proposed_asset.asset_class,
        portfolio_weight=input_data.proposed_weight,
        theme_tags=input_data.proposed_asset.theme_tags,
        is_speculative=input_data.proposed_asset.is_speculative,
    )
    proposed_positions = _positions_after_proposal(
        input_data.current_positions,
        input_data.proposed_asset.symbol,
        proposed_position,
    )
    exposures = _summarize_exposures(proposed_positions)

    warnings: list[str] = []
    violations: list[str] = []
    rationale: list[str] = []

    positive_signal = _positive_signal(input_data)
    risk_off = input_data.macro_regime.risk_sentiment.lower() in {"risk_off", "recession"} or (
        input_data.macro_regime.growth_regime.lower() == "recession"
    )

    if exposures.portfolio_total > 1.0001:
        warnings.append("Proposed weights exceed 100%; funding source or offsetting trim is not specified.")

    core_equity_rule = _find_rule(input_data.policy_rules, "core_equity_minimum")
    if core_equity_rule and core_equity_rule.minimum_weight is not None:
        if exposures.core_equity < core_equity_rule.minimum_weight:
            violations.append(
                f"Core broad equity falls below {core_equity_rule.minimum_weight:.0%} minimum."
            )
        else:
            rationale.append(
                f"Core broad equity remains at {exposures.core_equity:.1%}, above the policy floor."
            )

    thematic_rule = _find_rule(input_data.policy_rules, "thematic_exposure_cap")
    if thematic_rule and thematic_rule.hard_cap is not None:
        if exposures.thematic > thematic_rule.hard_cap:
            violations.append(
                f"Total thematic exposure would rise to {exposures.thematic:.1%}, above the {thematic_rule.hard_cap:.0%} cap."
            )

    ai_rule = _find_rule(input_data.policy_rules, "ai_semis_cap")
    if ai_rule:
        if ai_rule.hard_cap is not None and exposures.ai_semis > ai_rule.hard_cap:
            violations.append(
                f"AI/semiconductors exposure would rise to {exposures.ai_semis:.1%}, above the {ai_rule.hard_cap:.0%} cap."
            )
        elif ai_rule.soft_cap is not None and exposures.ai_semis >= ai_rule.soft_cap:
            warnings.append(
                f"AI/semiconductors exposure is near the policy cap at {exposures.ai_semis:.1%}."
            )
        else:
            rationale.append("AI/semiconductors exposure remains inside policy limits.")

    nuclear_rule = _find_rule(input_data.policy_rules, "nuclear_uranium_cap")
    if nuclear_rule:
        if nuclear_rule.hard_cap is not None and exposures.nuclear_uranium > nuclear_rule.hard_cap:
            violations.append(
                f"Nuclear/uranium exposure would rise to {exposures.nuclear_uranium:.1%}, above the {nuclear_rule.hard_cap:.0%} cap."
            )
        elif nuclear_rule.soft_cap is not None and exposures.nuclear_uranium >= nuclear_rule.soft_cap:
            warnings.append(
                f"Nuclear/uranium exposure is near the policy cap at {exposures.nuclear_uranium:.1%}."
            )

    metals_rule = _find_rule(input_data.policy_rules, "precious_metals_target")
    if metals_rule:
        if metals_rule.hard_cap is not None and exposures.precious_metals > metals_rule.hard_cap:
            violations.append(
                f"Precious metals exposure would rise to {exposures.precious_metals:.1%}, above the {metals_rule.hard_cap:.0%} hard cap."
            )
        elif metals_rule.soft_cap is not None and exposures.precious_metals > metals_rule.soft_cap:
            warnings.append(
                f"Precious metals exposure would move above the 5% target to {exposures.precious_metals:.1%}."
            )
        else:
            rationale.append("Precious metals exposure remains inside the policy band.")

    crypto_rule = _find_rule(input_data.policy_rules, "crypto_cap")
    if crypto_rule and crypto_rule.hard_cap is not None:
        if not input_data.profile.use_crypto and "crypto" in input_data.proposed_asset.theme_tags:
            violations.append("Profile disables crypto exposure.")
        elif exposures.crypto > crypto_rule.hard_cap:
            violations.append(
                f"Crypto exposure would rise to {exposures.crypto:.1%}, above the {crypto_rule.hard_cap:.0%} hard cap."
            )

    bonds_rule = _find_rule(input_data.policy_rules, "bonds_cash_minimum")
    if bonds_rule and bonds_rule.minimum_weight is not None:
        if exposures.bonds_cash < bonds_rule.minimum_weight:
            violations.append(
                f"Bonds/cash would fall to {exposures.bonds_cash:.1%}, below the {bonds_rule.minimum_weight:.0%} minimum."
            )
        else:
            rationale.append(
                f"Bonds/cash remain at {exposures.bonds_cash:.1%}, above the liquidity minimum."
            )

    if proposed_position.asset_class in {PortfolioAssetClass.EQUITY, PortfolioAssetClass.CRYPTO}:
        if input_data.proposed_weight > input_data.profile.single_stock_hard_cap:
            violations.append(
                f"Single-name exposure exceeds the {input_data.profile.single_stock_hard_cap:.0%} hard cap."
            )
        elif input_data.proposed_weight > input_data.profile.single_stock_soft_cap:
            warnings.append(
                f"Single-name exposure is above the {input_data.profile.single_stock_soft_cap:.0%} target."
            )

    speculative_rule = _find_rule(input_data.policy_rules, "speculative_single_name_cap")
    if speculative_rule and speculative_rule.hard_cap is not None:
        if proposed_position.is_speculative and input_data.proposed_weight > speculative_rule.hard_cap:
            violations.append(
                f"Speculative single-name exposure exceeds the {speculative_rule.hard_cap:.1%} cap."
            )

    if risk_off:
        warnings.append("Current macro regime is risk-off/recessionary; aggressive growth exposure should be sized cautiously.")
        rationale.append("Risk-off regime increases the hurdle rate for adding volatile assets.")
        if "crypto" in proposed_position.theme_tags:
            warnings.append("Crypto exposure is being proposed during a risk-off regime.")
        if proposed_position.is_speculative or "ai_semis" in proposed_position.theme_tags or "nuclear_uranium" in proposed_position.theme_tags:
            warnings.append("High-beta thematic exposure is less attractive in the current regime.")

    if input_data.data_is_stale or input_data.macro_regime.stale_data:
        warnings.append("Data freshness is stale; refresh market and macro inputs before acting.")

    if input_data.above_sma200 is False and positive_signal:
        warnings.append("Price remains below SMA200 despite a positive narrative or signal.")

    if positive_signal:
        rationale.append("Model signal is constructive, but policy and regime constraints still govern the final action.")

    decision = PolicyDecision.BLOCK if violations else PolicyDecision.WARN if warnings else PolicyDecision.ALLOW
    risk_level = _risk_level(violations, warnings, proposed_position, risk_off)

    return RiskEvaluationResult(
        allowed=decision != PolicyDecision.BLOCK,
        decision=decision,
        riskLevel=risk_level,
        violations=violations,
        warnings=warnings,
        rationale=rationale,
        adjustedRecommendation=_adjusted_recommendation(
            decision,
            warnings,
            violations,
            proposed_position,
            positive_signal,
        ),
    )
