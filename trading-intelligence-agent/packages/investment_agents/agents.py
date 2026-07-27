"""Definitions for the four bounded OpenAI Agents SDK research agents."""
from __future__ import annotations

import os

from agents import Agent, ModelSettings

from packages.investment_agents.guardrails import dossier_output_guardrail, research_request_guardrail
from packages.investment_agents.models import (
    EvidenceAnalystReport,
    InvestmentCommitteeDossier,
    RiskValuationReport,
    ThemeScoutReport,
)
from packages.investment_agents.tools import (
    calculate_portfolio_overlap,
    calculate_transparent_score,
    inspect_evidence_bundle,
)

DEFAULT_MODEL = os.getenv("OPENAI_AGENTS_MODEL", "gpt-5-mini")

_COMMON_RULES = """
You are part of a long-horizon investment research system.
Use only evidence supplied in the request or returned by tools. Never invent filings,
financial values, dates, sources, market prices, or citations. Social narratives are idea
sources, not proof. Distinguish facts, inferences, and missing data. Do not issue buy/sell
instructions, promise returns, or claim certainty. Outputs are research for human review.
Every evidence reference must use an evidence_id present in the supplied bundle.
"""


def build_theme_scout() -> Agent:
    return Agent(
        name="Theme Scout",
        model=DEFAULT_MODEL,
        instructions=_COMMON_RULES + """
Identify the structural theme, its causal drivers, and the candidate's plausible beneficiary
pathway. Be skeptical of buzzword exposure. Surface competitors and hype/crowding risks.
Do not perform valuation analysis or recommend a trade.
""",
        tools=[inspect_evidence_bundle],
        output_type=ThemeScoutReport,
        input_guardrails=[research_request_guardrail],
        model_settings=ModelSettings(temperature=0.2),
    )


def build_evidence_analyst() -> Agent:
    return Agent(
        name="Evidence Analyst",
        model=DEFAULT_MODEL,
        instructions=_COMMON_RULES + """
Verify whether the candidate has measurable exposure through revenue, segments, backlog,
customers, products, capex, margins, or filings. Classify exposure as proven,
partially_proven, or unproven. Unsupported marketing language must be listed explicitly.
Scores must reflect the evidence bundle rather than general model knowledge.
""",
        tools=[inspect_evidence_bundle],
        output_type=EvidenceAnalystReport,
        model_settings=ModelSettings(temperature=0.1),
    )


def build_risk_valuation_analyst() -> Agent:
    return Agent(
        name="Risk and Valuation Analyst",
        model=DEFAULT_MODEL,
        instructions=_COMMON_RULES + """
Act as the red team. Evaluate embedded expectations, valuation uncertainty, financial,
cyclical, regulatory, geopolitical, concentration, dilution, and portfolio-overlap risks.
Construct distinct bull, base, and bear cases. Define observable invalidation conditions.
A missing valuation dataset is a data gap, never permission to invent a multiple.
""",
        tools=[inspect_evidence_bundle, calculate_portfolio_overlap],
        output_type=RiskValuationReport,
        model_settings=ModelSettings(temperature=0.1),
    )


def build_committee_manager() -> Agent:
    return Agent(
        name="Investment Committee Manager",
        model=DEFAULT_MODEL,
        instructions=_COMMON_RULES + """
Synthesize the three specialist reports into one auditable dossier. Resolve disagreement
conservatively. Exposure must be proven before advancing. High valuation uncertainty,
weak evidence, excessive risk, or portfolio overlap must lower status. Use only these
statuses: advance_to_deeper_research, watchlist_needs_trigger, valuation_gated,
exposure_not_proven, portfolio_overlap_concern, risk_exceeds_reward, reject.
Never collapse the analysis into a buy/sell instruction. Preserve unresolved questions and
specify the next evidence needed.
""",
        tools=[calculate_transparent_score],
        output_type=InvestmentCommitteeDossier,
        output_guardrails=[dossier_output_guardrail],
        model_settings=ModelSettings(temperature=0.1),
    )
