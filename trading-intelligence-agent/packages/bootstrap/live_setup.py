"""Live bootstrap flow that seeds assets/watchlists without demo fixtures."""
from __future__ import annotations

import os
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from sqlalchemy import delete

from packages.core_models.db_tables import WatchlistTable
from packages.policy.defaults import (
    ASSET_UNIVERSE,
    DEFAULT_POLICY_RULES,
    DEFAULT_PORTFOLIO_POSITIONS,
    DEFAULT_PROFILE,
)
from packages.policy.models import PortfolioAssetClass
from packages.storage.database import create_tables
from packages.storage.repositories import (
    AssetRepository,
    PortfolioPolicyRepository,
    PortfolioProfileRepository,
)

_UNIVERSE_BY_SYMBOL = {str(asset["symbol"]).upper(): asset for asset in ASSET_UNIVERSE}
_SPOT_CRYPTO_ASSETS: dict[str, dict[str, Any]] = {
    "BTC-USD": {
        "name": "Bitcoin / USD",
        "asset_class": PortfolioAssetClass.CRYPTO,
        "sector": "Crypto",
        "theme_tags": ["crypto", "spot_crypto"],
        "is_speculative": False,
    },
    "ETH-USD": {
        "name": "Ethereum / USD",
        "asset_class": PortfolioAssetClass.CRYPTO,
        "sector": "Crypto",
        "theme_tags": ["crypto", "spot_crypto"],
        "is_speculative": False,
    },
    "SOL-USD": {
        "name": "Solana / USD",
        "asset_class": PortfolioAssetClass.CRYPTO,
        "sector": "Crypto",
        "theme_tags": ["crypto", "spot_crypto"],
        "is_speculative": True,
    },
    "BNB-USD": {
        "name": "BNB / USD",
        "asset_class": PortfolioAssetClass.CRYPTO,
        "sector": "Crypto",
        "theme_tags": ["crypto", "spot_crypto"],
        "is_speculative": True,
    },
}
SUPPORTED_DEFAULT_WATCHLIST = [
    "VOO",
    "VXUS",
    "QQQM",
    "SMH",
    "NLR",
    "GLD",
    "IBIT",
    "SGOV",
    "BTC-USD",
    "ETH-USD",
]


@dataclass(frozen=True)
class BootstrapAsset:
    symbol: str
    name: str
    asset_class: Any
    exchange: str
    currency: str = "USD"
    sector: str | None = None
    industry: str | None = None
    theme_tags: list[str] | None = None
    is_speculative: bool = False


def _default_watchlist() -> list[str]:
    return [
        symbol.strip().upper()
        for symbol in os.getenv(
            "DEFAULT_WATCHLIST",
            ",".join(SUPPORTED_DEFAULT_WATCHLIST),
        ).split(",")
        if symbol.strip()
    ]


def _build_universe_asset(symbol: str, payload: dict[str, Any]) -> BootstrapAsset:
    asset_class = payload["asset_class"]
    exchange = "CRYPTO" if asset_class == PortfolioAssetClass.CRYPTO else "NASDAQ"
    sector = payload.get("sector")
    return BootstrapAsset(
        symbol=symbol,
        name=str(payload["name"]),
        asset_class=asset_class,
        exchange=exchange,
        sector=str(sector) if sector is not None else None,
        industry=str(sector) if sector is not None else None,
        theme_tags=list(payload.get("theme_tags", [])),
        is_speculative=bool(payload.get("is_speculative", False)),
    )


def resolve_bootstrap_asset(symbol: str) -> BootstrapAsset:
    normalized = symbol.strip().upper()
    payload = _UNIVERSE_BY_SYMBOL.get(normalized)
    if payload is not None:
        return _build_universe_asset(normalized, payload)

    crypto_payload = _SPOT_CRYPTO_ASSETS.get(normalized)
    if crypto_payload is not None:
        return BootstrapAsset(
            symbol=normalized,
            name=str(crypto_payload["name"]),
            asset_class=crypto_payload["asset_class"],
            exchange="CRYPTO",
            sector=str(crypto_payload["sector"]),
            industry=str(crypto_payload["sector"]),
            theme_tags=list(crypto_payload["theme_tags"]),
            is_speculative=bool(crypto_payload["is_speculative"]),
        )

    raise ValueError(
        f"Unsupported bootstrap symbol '{normalized}'. Add it to ASSET_UNIVERSE or _SPOT_CRYPTO_ASSETS first."
    )


def resolve_bootstrap_assets(
    watchlist_symbols: list[str] | None = None,
    include_full_universe: bool = True,
) -> list[BootstrapAsset]:
    resolved: dict[str, BootstrapAsset] = {}

    if include_full_universe:
        for symbol, payload in _UNIVERSE_BY_SYMBOL.items():
            resolved[symbol] = _build_universe_asset(symbol, payload)

    for symbol in (watchlist_symbols or _default_watchlist()):
        asset = resolve_bootstrap_asset(symbol)
        resolved[asset.symbol] = asset

    return list(resolved.values())


async def bootstrap_live_environment(
    db_session_factory: Any,
    watchlist_symbols: list[str] | None = None,
    *,
    include_full_universe: bool = True,
    reset_watchlist: bool = False,
) -> dict[str, Any]:
    await create_tables()

    requested_watchlist = [symbol.strip().upper() for symbol in (watchlist_symbols or _default_watchlist()) if symbol.strip()]
    target_watchlist: list[str] = []
    watchlist_skipped: list[str] = []
    for symbol in requested_watchlist:
        try:
            resolve_bootstrap_asset(symbol)
        except ValueError:
            watchlist_skipped.append(symbol)
            continue
        target_watchlist.append(symbol)

    if not target_watchlist and watchlist_symbols is None:
        target_watchlist = list(SUPPORTED_DEFAULT_WATCHLIST)

    assets = resolve_bootstrap_assets(target_watchlist, include_full_universe=include_full_universe)

    async with db_session_factory() as db:
        asset_repo = AssetRepository(db)
        profile_repo = PortfolioProfileRepository(db)
        policy_repo = PortfolioPolicyRepository(db)

        upserted_assets: list[str] = []
        for asset in assets:
            row = await asset_repo.upsert(
                SimpleNamespace(
                    symbol=asset.symbol,
                    name=asset.name,
                    asset_class=asset.asset_class,
                    exchange=asset.exchange,
                    currency=asset.currency,
                    sector=asset.sector,
                    industry=asset.industry,
                    theme_tags=asset.theme_tags or [],
                    metadata={"is_speculative": asset.is_speculative, "bootstrap_source": "live_setup"},
                    is_active=True,
                )
            )
            upserted_assets.append(row.symbol)

        if reset_watchlist:
            await db.execute(delete(WatchlistTable))
            await db.commit()

        existing_symbols = {row.symbol for row in await asset_repo.get_watchlist()}
        watchlist_added: list[str] = []
        watchlist_existing: list[str] = []
        for symbol in target_watchlist:
            asset = await asset_repo.get_by_symbol(symbol)
            if asset is None:
                raise ValueError(f"Watchlist symbol {symbol} could not be created during bootstrap")
            if symbol in existing_symbols:
                watchlist_existing.append(symbol)
                continue
            await asset_repo.add_to_watchlist(asset.id, notes="Live bootstrap default watchlist")
            watchlist_added.append(symbol)

        profile_row = await profile_repo.upsert(DEFAULT_PROFILE)
        existing_positions = await profile_repo.get_positions(profile_row.id)
        if not existing_positions:
            await profile_repo.set_positions(profile_row.id, DEFAULT_PORTFOLIO_POSITIONS)
        existing_rules = await policy_repo.get_rules(profile_row.id)
        if not existing_rules:
            await policy_repo.replace_rules(profile_row.id, DEFAULT_POLICY_RULES)

        await db.commit()

    return {
        "status": "complete",
        "mode": "live_bootstrap",
        "full_universe_seeded": include_full_universe,
        "watchlist_reset": reset_watchlist,
        "assets_upserted_count": len(upserted_assets),
        "watchlist_added": watchlist_added,
        "watchlist_existing": watchlist_existing,
        "watchlist_skipped": watchlist_skipped,
        "watchlist_target": target_watchlist,
        "profile_name": DEFAULT_PROFILE.name,
    }
