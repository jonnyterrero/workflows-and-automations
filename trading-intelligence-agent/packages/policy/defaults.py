"""Default portfolio policy, asset universe, and demo positions."""
from __future__ import annotations

from packages.policy.models import (
    PolicyRule,
    PortfolioAssetClass,
    PortfolioPosition,
    PortfolioProfile,
    PortfolioRiskBucket,
)


def _asset(
    symbol: str,
    name: str,
    asset_class: PortfolioAssetClass,
    *,
    sector: str | None = None,
    theme_tags: list[str] | None = None,
    is_speculative: bool = False,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "name": name,
        "asset_class": asset_class,
        "sector": sector,
        "theme_tags": theme_tags or [],
        "is_speculative": is_speculative,
    }


ASSET_UNIVERSE: list[dict[str, object]] = [
    _asset("VOO", "Vanguard S&P 500 ETF", PortfolioAssetClass.ETF, sector="Broad Market", theme_tags=["core_equity", "us_broad_equity"]),
    _asset("VT", "Vanguard Total World Stock ETF", PortfolioAssetClass.ETF, sector="Broad Market", theme_tags=["core_equity", "global_equity"]),
    _asset("VXUS", "Vanguard Total International Stock ETF", PortfolioAssetClass.ETF, sector="Broad Market", theme_tags=["core_equity", "global_ex_us"]),
    _asset("QQQM", "Invesco NASDAQ 100 ETF", PortfolioAssetClass.ETF, sector="Technology", theme_tags=["growth_tilt"]),
    _asset("BND", "Vanguard Total Bond Market ETF", PortfolioAssetClass.BOND, sector="Fixed Income", theme_tags=["bonds_cash"]),
    _asset("TIP", "iShares TIPS Bond ETF", PortfolioAssetClass.BOND, sector="Fixed Income", theme_tags=["bonds_cash", "inflation_hedge"]),
    _asset("BIL", "SPDR 1-3 Month T-Bill ETF", PortfolioAssetClass.CASH_EQUIVALENT, sector="Cash", theme_tags=["bonds_cash", "tbills"]),
    _asset("SGOV", "iShares 0-3 Month Treasury Bond ETF", PortfolioAssetClass.CASH_EQUIVALENT, sector="Cash", theme_tags=["bonds_cash", "tbills"]),
    _asset("NVDA", "NVIDIA Corporation", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("TSM", "Taiwan Semiconductor Manufacturing", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("ASML", "ASML Holding", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("AVGO", "Broadcom Inc.", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("AMD", "Advanced Micro Devices", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("MU", "Micron Technology", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("LRCX", "Lam Research", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("AMAT", "Applied Materials", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("TXN", "Texas Instruments", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("ON", "ON Semiconductor", PortfolioAssetClass.EQUITY, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("SMH", "VanEck Semiconductor ETF", PortfolioAssetClass.ETF, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("SOXX", "iShares Semiconductor ETF", PortfolioAssetClass.ETF, sector="Semiconductors", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("MSFT", "Microsoft Corporation", PortfolioAssetClass.EQUITY, sector="Software", theme_tags=["cloud_saas", "thematic_tech"]),
    _asset("AMZN", "Amazon.com, Inc.", PortfolioAssetClass.EQUITY, sector="Cloud", theme_tags=["cloud_saas", "thematic_tech"]),
    _asset("GOOG", "Alphabet Inc.", PortfolioAssetClass.EQUITY, sector="Cloud", theme_tags=["cloud_saas", "thematic_tech"]),
    _asset("NOW", "ServiceNow", PortfolioAssetClass.EQUITY, sector="Software", theme_tags=["cloud_saas", "thematic_tech"]),
    _asset("SNOW", "Snowflake", PortfolioAssetClass.EQUITY, sector="Software", theme_tags=["cloud_saas", "thematic_tech"], is_speculative=True),
    _asset("CRWD", "CrowdStrike", PortfolioAssetClass.EQUITY, sector="Cybersecurity", theme_tags=["cybersecurity", "thematic_tech"]),
    _asset("PANW", "Palo Alto Networks", PortfolioAssetClass.EQUITY, sector="Cybersecurity", theme_tags=["cybersecurity", "thematic_tech"]),
    _asset("ZS", "Zscaler", PortfolioAssetClass.EQUITY, sector="Cybersecurity", theme_tags=["cybersecurity", "thematic_tech"], is_speculative=True),
    _asset("FTNT", "Fortinet", PortfolioAssetClass.EQUITY, sector="Cybersecurity", theme_tags=["cybersecurity", "thematic_tech"]),
    _asset("SKYY", "First Trust Cloud Computing ETF", PortfolioAssetClass.ETF, sector="Cloud", theme_tags=["cloud_saas", "thematic_tech"]),
    _asset("BUG", "Global X Cybersecurity ETF", PortfolioAssetClass.ETF, sector="Cybersecurity", theme_tags=["cybersecurity", "thematic_tech"]),
    _asset("BOTZ", "Global X Robotics & AI ETF", PortfolioAssetClass.ETF, sector="Robotics", theme_tags=["ai_semis", "thematic_tech"]),
    _asset("CEG", "Constellation Energy", PortfolioAssetClass.EQUITY, sector="Energy", theme_tags=["energy_power_nuclear", "nuclear_uranium"]),
    _asset("NEE", "NextEra Energy", PortfolioAssetClass.EQUITY, sector="Utilities", theme_tags=["energy_power_nuclear", "regulated_utilities"]),
    _asset("DUK", "Duke Energy", PortfolioAssetClass.EQUITY, sector="Utilities", theme_tags=["energy_power_nuclear", "regulated_utilities"]),
    _asset("SO", "Southern Company", PortfolioAssetClass.EQUITY, sector="Utilities", theme_tags=["energy_power_nuclear", "regulated_utilities"]),
    _asset("CCJ", "Cameco Corporation", PortfolioAssetClass.EQUITY, sector="Uranium", theme_tags=["energy_power_nuclear", "nuclear_uranium"]),
    _asset("NXE", "NexGen Energy", PortfolioAssetClass.EQUITY, sector="Uranium", theme_tags=["energy_power_nuclear", "nuclear_uranium"], is_speculative=True),
    _asset("UUUU", "Energy Fuels", PortfolioAssetClass.EQUITY, sector="Uranium", theme_tags=["energy_power_nuclear", "nuclear_uranium"], is_speculative=True),
    _asset("OKLO", "Oklo", PortfolioAssetClass.EQUITY, sector="Nuclear", theme_tags=["energy_power_nuclear", "nuclear_uranium"], is_speculative=True),
    _asset("NNE", "Nano Nuclear Energy", PortfolioAssetClass.EQUITY, sector="Nuclear", theme_tags=["energy_power_nuclear", "nuclear_uranium"], is_speculative=True),
    _asset("URA", "Global X Uranium ETF", PortfolioAssetClass.ETF, sector="Uranium", theme_tags=["energy_power_nuclear", "nuclear_uranium"]),
    _asset("NLR", "VanEck Uranium and Nuclear ETF", PortfolioAssetClass.ETF, sector="Nuclear", theme_tags=["energy_power_nuclear", "nuclear_uranium"]),
    _asset("DTCR", "Global X Data Center & Digital Infrastructure ETF", PortfolioAssetClass.ETF, sector="Infrastructure", theme_tags=["grid_infrastructure"]),
    _asset("IAU", "iShares Gold Trust", PortfolioAssetClass.METAL, sector="Precious Metals", theme_tags=["precious_metals", "gold"]),
    _asset("GLD", "SPDR Gold Shares", PortfolioAssetClass.METAL, sector="Precious Metals", theme_tags=["precious_metals", "gold"]),
    _asset("SLV", "iShares Silver Trust", PortfolioAssetClass.METAL, sector="Precious Metals", theme_tags=["precious_metals", "silver"]),
    _asset("BTC", "Bitcoin", PortfolioAssetClass.CRYPTO, sector="Crypto", theme_tags=["crypto"]),
    _asset("ETH", "Ethereum", PortfolioAssetClass.CRYPTO, sector="Crypto", theme_tags=["crypto"]),
    _asset("IBIT", "iShares Bitcoin Trust", PortfolioAssetClass.ETF, sector="Crypto", theme_tags=["crypto"]),
    _asset("FBTC", "Fidelity Wise Origin Bitcoin Fund", PortfolioAssetClass.ETF, sector="Crypto", theme_tags=["crypto"]),
    _asset("ARKB", "ARK 21Shares Bitcoin ETF", PortfolioAssetClass.ETF, sector="Crypto", theme_tags=["crypto"]),
    _asset("GBTC", "Grayscale Bitcoin Trust", PortfolioAssetClass.ETF, sector="Crypto", theme_tags=["crypto"]),
    _asset("ETHA", "iShares Ethereum Trust", PortfolioAssetClass.ETF, sector="Crypto", theme_tags=["crypto"]),
    _asset("ETHV", "VanEck Ethereum ETF", PortfolioAssetClass.ETF, sector="Crypto", theme_tags=["crypto"]),
    _asset("COIN", "Coinbase Global", PortfolioAssetClass.EQUITY, sector="Crypto Equity", theme_tags=["crypto", "crypto_equity"], is_speculative=True),
    _asset("MSTR", "MicroStrategy", PortfolioAssetClass.EQUITY, sector="Crypto Equity", theme_tags=["crypto", "crypto_equity"], is_speculative=True),
    _asset("BITO", "ProShares Bitcoin Strategy ETF", PortfolioAssetClass.ETF, sector="Crypto", theme_tags=["crypto"], is_speculative=True),
]


DEFAULT_PROFILE = PortfolioProfile(
    name="Aggressive Long-Term Growth",
    risk_bucket=PortfolioRiskBucket.AGGRESSIVE,
    time_horizon_years=10,
    max_drawdown_tolerance=0.30,
    use_crypto=True,
    use_precious_metals=True,
    min_liquidity_months=6,
    avoid_leverage=True,
    single_stock_soft_cap=0.03,
    single_stock_hard_cap=0.05,
    notes="Default profile seeded from the cross-asset policy prompt.",
)


DEFAULT_POLICY_RULES: list[PolicyRule] = [
    PolicyRule(rule_name="core_equity_minimum", rule_type="theme_target", minimum_weight=0.50, theme_tag="core_equity"),
    PolicyRule(rule_name="thematic_exposure_cap", rule_type="theme_cap", hard_cap=0.35, theme_tag="thematic_tech"),
    PolicyRule(rule_name="ai_semis_cap", rule_type="theme_cap", soft_cap=0.14, hard_cap=0.15, theme_tag="ai_semis"),
    PolicyRule(rule_name="nuclear_uranium_cap", rule_type="theme_cap", soft_cap=0.07, hard_cap=0.08, theme_tag="nuclear_uranium"),
    PolicyRule(rule_name="precious_metals_target", rule_type="theme_target", target_weight=0.05, soft_cap=0.05, hard_cap=0.10, theme_tag="precious_metals"),
    PolicyRule(rule_name="crypto_cap", rule_type="theme_cap", hard_cap=0.08, theme_tag="crypto"),
    PolicyRule(rule_name="bonds_cash_minimum", rule_type="theme_target", minimum_weight=0.10, theme_tag="bonds_cash"),
    PolicyRule(rule_name="single_position_etf_cap", rule_type="single_position_cap", hard_cap=0.10),
    PolicyRule(rule_name="single_stock_target_cap", rule_type="single_position_target", soft_cap=0.03),
    PolicyRule(rule_name="single_stock_hard_cap", rule_type="single_position_cap", hard_cap=0.05),
    PolicyRule(rule_name="speculative_single_name_cap", rule_type="speculative_cap", hard_cap=0.015),
]


DEFAULT_PORTFOLIO_POSITIONS: list[PortfolioPosition] = [
    PortfolioPosition(symbol="VOO", asset_class=PortfolioAssetClass.ETF, portfolio_weight=0.35, theme_tags=["core_equity", "us_broad_equity"]),
    PortfolioPosition(symbol="VXUS", asset_class=PortfolioAssetClass.ETF, portfolio_weight=0.10, theme_tags=["core_equity", "global_ex_us"]),
    PortfolioPosition(symbol="QQQM", asset_class=PortfolioAssetClass.ETF, portfolio_weight=0.10, theme_tags=["growth_tilt"]),
    PortfolioPosition(symbol="SMH", asset_class=PortfolioAssetClass.ETF, portfolio_weight=0.08, theme_tags=["ai_semis", "thematic_tech"]),
    PortfolioPosition(symbol="NLR", asset_class=PortfolioAssetClass.ETF, portfolio_weight=0.05, theme_tags=["energy_power_nuclear", "nuclear_uranium"]),
    PortfolioPosition(symbol="GLD", asset_class=PortfolioAssetClass.METAL, portfolio_weight=0.04, theme_tags=["precious_metals", "gold"]),
    PortfolioPosition(symbol="SLV", asset_class=PortfolioAssetClass.METAL, portfolio_weight=0.01, theme_tags=["precious_metals", "silver"]),
    PortfolioPosition(symbol="IBIT", asset_class=PortfolioAssetClass.ETF, portfolio_weight=0.05, theme_tags=["crypto"]),
    PortfolioPosition(symbol="ETHA", asset_class=PortfolioAssetClass.ETF, portfolio_weight=0.02, theme_tags=["crypto"]),
    PortfolioPosition(symbol="BND", asset_class=PortfolioAssetClass.BOND, portfolio_weight=0.05, theme_tags=["bonds_cash"]),
    PortfolioPosition(symbol="SGOV", asset_class=PortfolioAssetClass.CASH_EQUIVALENT, portfolio_weight=0.05, theme_tags=["bonds_cash", "tbills"]),
]
