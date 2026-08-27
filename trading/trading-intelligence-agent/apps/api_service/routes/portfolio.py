"""Portfolio profile, policy, and pure decision-evaluation routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.policy.defaults import DEFAULT_POLICY_RULES, DEFAULT_PORTFOLIO_POSITIONS, DEFAULT_PROFILE
from packages.policy.evaluator import evaluate_portfolio_decision
from packages.policy.models import (
    AssetCandidate,
    MacroRegime,
    PolicyRule,
    PortfolioDecisionInput,
    PortfolioPosition,
    PortfolioProfile,
    SignalOutput,
)
from packages.storage.database import get_db
from packages.storage.repositories import (
    AssetRepository,
    PortfolioPolicyRepository,
    PortfolioProfileRepository,
)

router = APIRouter()


class PortfolioProfileUpdateRequest(BaseModel):
    profile: PortfolioProfile
    positions: list[PortfolioPosition] = Field(default_factory=list)
    rules: list[PolicyRule] | None = None


class PortfolioEvaluateRequest(BaseModel):
    symbol: str
    proposed_weight: float = Field(ge=0.0, le=1.0)
    profile_id: int | None = None
    macro_regime: MacroRegime = Field(default_factory=MacroRegime)
    model_signal: SignalOutput | None = None
    data_is_stale: bool = False
    above_sma200: bool | None = None


def _profile_row_to_model(row) -> PortfolioProfile:
    return PortfolioProfile(
        id=row.id,
        name=row.name,
        risk_bucket=row.risk_bucket,
        time_horizon_years=row.time_horizon_years,
        max_drawdown_tolerance=row.max_drawdown_tolerance,
        use_crypto=row.use_crypto,
        use_precious_metals=row.use_precious_metals,
        min_liquidity_months=row.min_liquidity_months,
        avoid_leverage=row.avoid_leverage,
        single_stock_soft_cap=row.single_stock_soft_cap,
        single_stock_hard_cap=row.single_stock_hard_cap,
        notes=row.notes,
    )


def _position_row_to_model(row) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=row.symbol,
        asset_class=row.asset_class,
        portfolio_weight=row.portfolio_weight,
        quantity=row.quantity,
        market_value=row.market_value,
        cost_basis=row.cost_basis,
        theme_tags=row.theme_tags or [],
        is_speculative=row.is_speculative,
    )


def _rule_row_to_model(row) -> PolicyRule:
    return PolicyRule(
        rule_name=row.rule_name,
        rule_type=row.rule_type,
        target_weight=row.target_weight,
        soft_cap=row.soft_cap,
        hard_cap=row.hard_cap,
        minimum_weight=row.minimum_weight,
        asset_class=row.asset_class,
        theme_tag=row.theme_tag,
        symbol=row.symbol,
        is_active=row.is_active,
    )


async def _ensure_default_portfolio(
    db: AsyncSession,
    requested_profile_id: int | None = None,
) -> tuple[PortfolioProfile, list[PortfolioPosition], list[PolicyRule]]:
    profile_repo = PortfolioProfileRepository(db)
    policy_repo = PortfolioPolicyRepository(db)

    row = await profile_repo.get_by_id(requested_profile_id) if requested_profile_id else await profile_repo.get_default()
    if row is None:
        row = await profile_repo.upsert(DEFAULT_PROFILE)
        await profile_repo.set_positions(row.id, DEFAULT_PORTFOLIO_POSITIONS)
        await policy_repo.replace_rules(row.id, DEFAULT_POLICY_RULES)

    profile = _profile_row_to_model(row)
    positions = [_position_row_to_model(item) for item in await profile_repo.get_positions(row.id)]
    rules = [_rule_row_to_model(item) for item in await policy_repo.get_rules(row.id)]

    if not positions:
        await profile_repo.set_positions(row.id, DEFAULT_PORTFOLIO_POSITIONS)
        positions = DEFAULT_PORTFOLIO_POSITIONS
    if not rules:
        await policy_repo.replace_rules(row.id, DEFAULT_POLICY_RULES)
        rules = DEFAULT_POLICY_RULES
    return profile, positions, rules


@router.get("/profile")
async def get_profile(
    profile_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile, positions, rules = await _ensure_default_portfolio(db, profile_id)
    return {
        "profile": profile.model_dump(),
        "positions": [position.model_dump() for position in positions],
        "rules": [rule.model_dump() for rule in rules],
    }


@router.put("/profile")
async def update_profile(
    body: PortfolioProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile_repo = PortfolioProfileRepository(db)
    policy_repo = PortfolioPolicyRepository(db)

    row = await profile_repo.upsert(body.profile)
    await profile_repo.set_positions(row.id, body.positions)
    await policy_repo.replace_rules(row.id, body.rules or DEFAULT_POLICY_RULES)

    profile = _profile_row_to_model(row)
    return {
        "profile": profile.model_dump(),
        "positions": [position.model_dump() for position in body.positions],
        "rules": [rule.model_dump() for rule in (body.rules or DEFAULT_POLICY_RULES)],
    }


@router.get("/policy")
async def get_policy(
    profile_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile, _positions, rules = await _ensure_default_portfolio(db, profile_id)
    return {
        "profileId": profile.id,
        "profileName": profile.name,
        "rules": [rule.model_dump() for rule in rules],
    }


@router.post("/evaluate")
async def evaluate_portfolio(
    body: PortfolioEvaluateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile, positions, rules = await _ensure_default_portfolio(db, body.profile_id)
    asset_repo = AssetRepository(db)
    asset_row = await asset_repo.get_by_symbol(body.symbol.upper())
    if asset_row is None:
        raise HTTPException(status_code=404, detail=f"Asset {body.symbol.upper()} not found in asset universe")

    proposed_asset = AssetCandidate(
        symbol=asset_row.symbol,
        name=asset_row.name,
        asset_class=asset_row.asset_class,
        theme_tags=asset_row.theme_tags or [],
        sector=asset_row.sector,
        is_speculative=(asset_row.metadata_json or {}).get("is_speculative", False),
    )
    result = evaluate_portfolio_decision(
        PortfolioDecisionInput(
            profile=profile,
            current_positions=positions,
            proposed_asset=proposed_asset,
            proposed_weight=body.proposed_weight,
            macro_regime=body.macro_regime,
            model_signal=body.model_signal,
            policy_rules=rules,
            data_is_stale=body.data_is_stale,
            above_sma200=body.above_sma200,
        )
    )
    return result.model_dump()
