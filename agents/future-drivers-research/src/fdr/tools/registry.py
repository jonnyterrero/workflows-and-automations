"""Custom tool registry — the contract between agents and the orchestrator.

These are Managed Agents *custom* tools, which means they execute here, in our
process, not in the agent's sandbox. The agent emits ``agent.custom_tool_use``;
the runner dispatches through this table and replies with
``user.custom_tool_result``.

That indirection is the security boundary: SEC, FRED, and market credentials
stay in the orchestrator and are never visible to sandboxed code, so a prompt
injection in a fetched filing cannot exfiltrate them.

``TOOL_SPECS`` is the single source of truth. The agent YAML files must declare
byte-identical schemas; ``tests/test_agent_definitions.py`` fails the build if
they drift.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fdr import scoring
from fdr.schemas import AssetDossier
from fdr.tools import changes, filings, journal, macro, market, portfolio

Handler = Callable[[dict[str, Any]], dict[str, Any]]

# Agent slugs, matching the filenames in agents/.
THEME_SCOUT = "theme-scout"
EVIDENCE_ANALYST = "evidence-analyst"
RISK_ANALYST = "risk-valuation-analyst"
COMMITTEE = "investment-committee"

_SYMBOL = {"type": "string", "description": "Ticker symbol, e.g. NVDA."}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Handler
    agents: tuple[str, ...] = field(default=())

    def definition(self) -> dict[str, Any]:
        """The shape Managed Agents expects in an agent's ``tools`` array."""
        return {
            "type": "custom",
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


# --- handlers -------------------------------------------------------------
# Thin adapters. Real logic lives in the tool modules so it stays unit-testable
# without constructing tool payloads.


def _h_recent_filings(payload: dict[str, Any]) -> dict[str, Any]:
    return filings.sec_recent_filings(
        payload["symbol"], payload.get("forms"), int(payload.get("limit", 5))
    )


def _h_company_facts(payload: dict[str, Any]) -> dict[str, Any]:
    return filings.sec_company_facts(payload["symbol"])


def _h_compute_fundamentals(payload: dict[str, Any]) -> dict[str, Any]:
    facts = filings.sec_company_facts(payload["symbol"])
    if "error" in facts:
        return facts
    ratios = market.compute_fundamentals(facts.get("facts", {}))
    return {
        "symbol": facts["symbol"],
        "source_tier": 1,
        "source_name": facts.get("source_name"),
        "ratios": ratios,
        "demo_mode": facts.get("demo_mode", False),
    }


def _h_fred_series(payload: dict[str, Any]) -> dict[str, Any]:
    return macro.fred_series(payload["series_id"], int(payload.get("observations", 12)))


def _h_market_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    return market.get_market_snapshot(payload["symbol"])


def _h_valuation_context(payload: dict[str, Any]) -> dict[str, Any]:
    return market.valuation_context(payload["symbol"])


def _h_portfolio_overlap(payload: dict[str, Any]) -> dict[str, Any]:
    return portfolio.portfolio_overlap(
        payload.get("positions", []),
        payload["candidate"],
        float(payload.get("candidate_weight", 0.05)),
    )


def _h_score_dossier(payload: dict[str, Any]) -> dict[str, Any]:
    """Compute scores and research status from a draft dossier.

    The manager cannot assign its own scores; it submits evidence and receives
    numbers. Returned status is whatever the gates say, including outcomes the
    agent may not have wanted.
    """
    dossier = AssetDossier.model_validate(payload["dossier"])
    finalized = scoring.finalize(dossier)
    return {
        "symbol": finalized.symbol,
        "research_status": finalized.research_status.value,
        "scores": finalized.scores.model_dump() if finalized.scores else None,
        "penalties": finalized.penalties.model_dump(),
        "summary": scoring.explain(finalized.scores) if finalized.scores else "",
        "dossier": finalized.model_dump(mode="json"),
    }


def _h_save_dossier(payload: dict[str, Any]) -> dict[str, Any]:
    dossier = AssetDossier.model_validate(payload["dossier"])
    return journal.save_dossier(scoring.finalize(dossier))


def _h_load_dossier(payload: dict[str, Any]) -> dict[str, Any]:
    dossier = journal.load_dossier(payload["symbol"])
    if dossier is None:
        return {"symbol": payload["symbol"].upper(), "found": False}
    return {"symbol": dossier.symbol, "found": True, "dossier": dossier.model_dump(mode="json")}


def _h_detect_changes(payload: dict[str, Any]) -> dict[str, Any]:
    symbol = payload["symbol"]
    current = journal.load_dossier(symbol)
    previous = journal.load_previous_dossier(symbol)
    if current is None:
        return {"symbol": symbol.upper(), "error": "no current dossier stored"}
    if previous is None:
        return {"symbol": symbol.upper(), "total": 0, "changes": [], "note": "no prior snapshot"}
    return changes.summarize_changes(changes.detect_changes(previous, current))


def _h_record_decision(payload: dict[str, Any]) -> dict[str, Any]:
    return journal.record_decision(
        user_id=payload["user_id"],
        symbol=payload["symbol"],
        vote=payload["vote"],
        what_was_believed=payload["what_was_believed"],
        risks_accepted=payload.get("risks_accepted"),
        expected_horizon_months=payload.get("expected_horizon_months"),
        invalidation_conditions=payload.get("invalidation_conditions"),
    )


# --- specs ----------------------------------------------------------------

TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="fred_series",
        description=(
            "Fetch a Federal Reserve (FRED) macro time series with its recent trend. "
            "Tier 1 source. Use to establish that a capital-spending, rate, or policy "
            "cycle is actually underway rather than inferring it from news coverage."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "series_id": {
                    "type": "string",
                    "description": "FRED series ID, e.g. IPUTIL, NEWORDER, DGS10.",
                },
                "observations": {
                    "type": "integer",
                    "description": "How many recent observations to return. Default 12.",
                },
            },
            "required": ["series_id"],
        },
        handler=_h_fred_series,
        agents=(THEME_SCOUT,),
    ),
    ToolSpec(
        name="sec_recent_filings",
        description=(
            "List recent SEC EDGAR filings for a ticker. Tier 1 source. Use to locate "
            "the primary documents behind any claim about a company."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "symbol": _SYMBOL,
                "forms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Form types to include. Defaults to 10-K, 10-Q, 8-K.",
                },
                "limit": {"type": "integer", "description": "Max filings to return. Default 5."},
            },
            "required": ["symbol"],
        },
        handler=_h_recent_filings,
        agents=(EVIDENCE_ANALYST,),
    ),
    ToolSpec(
        name="sec_company_facts",
        description=(
            "Fetch structured XBRL financial facts a company actually reported to the "
            "SEC. Tier 1 source. Values are as-reported; a missing field means the "
            "company did not disclose it and must not be treated as zero."
        ),
        input_schema={
            "type": "object",
            "properties": {"symbol": _SYMBOL},
            "required": ["symbol"],
        },
        handler=_h_company_facts,
        agents=(EVIDENCE_ANALYST,),
    ),
    ToolSpec(
        name="compute_fundamentals",
        description=(
            "Compute margin, leverage, return, and free-cash-flow ratios from a "
            "company's reported SEC filings. Deterministic arithmetic — always use "
            "this instead of calculating ratios yourself, so every asset is measured "
            "identically."
        ),
        input_schema={
            "type": "object",
            "properties": {"symbol": _SYMBOL},
            "required": ["symbol"],
        },
        handler=_h_compute_fundamentals,
        agents=(EVIDENCE_ANALYST,),
    ),
    ToolSpec(
        name="get_market_snapshot",
        description=(
            "Fetch price, market cap, and trailing valuation multiples with their "
            "own five-year percentile. Tier 2 source."
        ),
        input_schema={
            "type": "object",
            "properties": {"symbol": _SYMBOL},
            "required": ["symbol"],
        },
        handler=_h_market_snapshot,
        agents=(RISK_ANALYST,),
    ),
    ToolSpec(
        name="valuation_context",
        description=(
            "Assess what expectations the current price appears to embed, expressed "
            "as percentiles against the asset's own history and its peer group, plus "
            "a 0-100 valuation score where cheap scores high."
        ),
        input_schema={
            "type": "object",
            "properties": {"symbol": _SYMBOL},
            "required": ["symbol"],
        },
        handler=_h_valuation_context,
        agents=(RISK_ANALYST,),
    ),
    ToolSpec(
        name="portfolio_overlap",
        description=(
            "Compute how much genuinely new exposure a candidate would add to a "
            "portfolio, decomposing every ETF into its underlying holdings. Surfaces "
            "concentration that is invisible at the ticker level."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "positions": {
                    "type": "array",
                    "description": "Current holdings as portfolio weights.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "weight": {
                                "type": "number",
                                "description": "Share of total portfolio, 0-1.",
                            },
                        },
                        "required": ["symbol", "weight"],
                    },
                },
                "candidate": {"type": "string", "description": "Ticker being considered."},
                "candidate_weight": {
                    "type": "number",
                    "description": "Proposed position size as a share of portfolio. Default 0.05.",
                },
            },
            "required": ["positions", "candidate"],
        },
        handler=_h_portfolio_overlap,
        agents=(RISK_ANALYST, COMMITTEE),
    ),
    ToolSpec(
        name="score_dossier",
        description=(
            "Submit a draft dossier and receive computed scores, risk penalties, and "
            "a research status. You must not assign scores yourself — supply the "
            "evidence and call this. Scores are gated by source tier, so claims "
            "backed only by commentary or social sources will be capped."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "dossier": {
                    "type": "object",
                    "description": "Draft AssetDossier object. Must include symbol and asset_class.",
                }
            },
            "required": ["dossier"],
        },
        handler=_h_score_dossier,
        agents=(COMMITTEE,),
    ),
    ToolSpec(
        name="save_dossier",
        description=(
            "Persist the final dossier and archive an immutable timestamped snapshot. "
            "Scores are recomputed on save, so stored numbers always match the "
            "stored evidence."
        ),
        input_schema={
            "type": "object",
            "properties": {"dossier": {"type": "object", "description": "Final AssetDossier object."}},
            "required": ["dossier"],
        },
        handler=_h_save_dossier,
        agents=(COMMITTEE,),
    ),
    ToolSpec(
        name="load_dossier",
        description="Load the most recently stored dossier for a symbol, if one exists.",
        input_schema={
            "type": "object",
            "properties": {"symbol": _SYMBOL},
            "required": ["symbol"],
        },
        handler=_h_load_dossier,
        agents=(COMMITTEE,),
    ),
    ToolSpec(
        name="detect_changes",
        description=(
            "Compare the current stored dossier against the previous snapshot and "
            "report what materially changed, including any invalidation condition "
            "that now appears to have been met."
        ),
        input_schema={
            "type": "object",
            "properties": {"symbol": _SYMBOL},
            "required": ["symbol"],
        },
        handler=_h_detect_changes,
        agents=(COMMITTEE,),
    ),
    ToolSpec(
        name="record_decision",
        description=(
            "Record a user's own research decision with the evidence that existed at "
            "the time. Only call this when a specific user has stated a decision — "
            "never infer one on their behalf."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "symbol": _SYMBOL,
                "vote": {
                    "type": "string",
                    "enum": ["research", "watch", "own", "avoid", "insufficient_evidence"],
                },
                "what_was_believed": {
                    "type": "string",
                    "description": "The thesis in the user's own terms.",
                },
                "risks_accepted": {"type": "array", "items": {"type": "string"}},
                "expected_horizon_months": {"type": "integer"},
                "invalidation_conditions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["user_id", "symbol", "vote", "what_was_believed"],
        },
        handler=_h_record_decision,
        agents=(COMMITTEE,),
    ),
)

REGISTRY: dict[str, ToolSpec] = {spec.name: spec for spec in TOOL_SPECS}


def tools_for(agent_slug: str) -> list[dict[str, Any]]:
    """Custom tool definitions an agent should declare."""
    return [spec.definition() for spec in TOOL_SPECS if agent_slug in spec.agents]


def dispatch(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Execute a custom tool call.

    Errors are returned rather than raised so the agent receives a usable
    result and can adapt, instead of the session stalling on an exception in
    our process.
    """
    spec = REGISTRY.get(name)
    if spec is None:
        return {"error": f"unknown tool '{name}'", "available": sorted(REGISTRY)}
    try:
        return spec.handler(payload)
    except Exception as exc:  # noqa: BLE001 - surfaced to the agent as a tool error
        return {"error": f"{type(exc).__name__}: {exc}", "tool": name}
