"""End-to-end orchestration for the four-agent investment research workflow."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import date

from agents import Runner, trace

from packages.investment_agents.agents import (
    build_committee_manager,
    build_evidence_analyst,
    build_risk_valuation_analyst,
    build_theme_scout,
)
from packages.investment_agents.guardrails import validate_request
from packages.investment_agents.models import (
    EvidenceAnalystReport,
    ExposureStatus,
    InvestmentCommitteeDossier,
    ResearchRequest,
    ResearchStatus,
    RiskValuationReport,
    ScoreCard,
    ThemeScoutReport,
)
from packages.investment_agents.tools import evidence_quality, overlap_risk


@dataclass(slots=True)
class SpecialistBundle:
    theme: ThemeScoutReport
    evidence: EvidenceAnalystReport
    risk: RiskValuationReport


class InvestmentResearchOrchestrator:
    """Run three bounded specialists and a final conservative committee synthesis."""

    def __init__(self) -> None:
        self.theme_scout = build_theme_scout()
        self.evidence_analyst = build_evidence_analyst()
        self.risk_analyst = build_risk_valuation_analyst()
        self.committee = build_committee_manager()

    async def run(self, request: ResearchRequest) -> InvestmentCommitteeDossier:
        request = validate_request(request)
        request_json = request.model_dump_json(indent=2)
        with trace("four-agent-investment-research", group_id=request.symbol):
            theme_result, evidence_result, risk_result = await asyncio.gather(
                Runner.run(self.theme_scout, request_json),
                Runner.run(self.evidence_analyst, request_json),
                Runner.run(self.risk_analyst, request_json),
            )
            bundle = SpecialistBundle(
                theme=theme_result.final_output,
                evidence=evidence_result.final_output,
                risk=risk_result.final_output,
            )
            committee_input = json.dumps(
                {
                    "request": request.model_dump(mode="json"),
                    "theme_scout_report": bundle.theme.model_dump(mode="json"),
                    "evidence_analyst_report": bundle.evidence.model_dump(mode="json"),
                    "risk_valuation_report": bundle.risk.model_dump(mode="json"),
                },
                indent=2,
                default=str,
            )
            result = await Runner.run(self.committee, committee_input)
            return result.final_output

    async def run_offline_demo(self, request: ResearchRequest) -> InvestmentCommitteeDossier:
        """Generate a deterministic demonstration without an API key or model call."""
        request = validate_request(request)
        quality = evidence_quality(request.evidence)
        overlap = overlap_risk(request.symbol, request.existing_positions)
        evidence_count = int(quality["count"])
        evidence_confidence = float(quality["weighted_quality"])
        exposure = 72.0 if evidence_count >= 2 else 45.0 if evidence_count == 1 else 15.0
        risk = min(95.0, 38.0 + float(overlap["score"]) * 0.35 + float(quality["freshness_penalty"]) * 0.25)
        valuation = 50.0  # Neutral because offline fixtures do not include a valuation dataset.

        if evidence_count == 0:
            status = ResearchStatus.EXPOSURE_UNPROVEN
            rejection = "No primary or structured evidence was supplied."
        elif float(overlap["score"]) >= 60:
            status = ResearchStatus.OVERLAP_CONCERN
            rejection = "Declared portfolio overlap is elevated and requires look-through analysis."
        elif risk >= 70:
            status = ResearchStatus.RISK_EXCEEDS_REWARD
            rejection = "Risk inputs are too elevated for advancement without stronger evidence."
        elif valuation <= 50:
            status = ResearchStatus.VALUATION_GATED
            rejection = "No current valuation dataset was supplied."
        else:
            status = ResearchStatus.WATCHLIST
            rejection = None

        ids = [item.evidence_id for item in request.evidence]
        return InvestmentCommitteeDossier(
            symbol=request.symbol,
            asset_name=request.asset_name,
            asset_class=request.asset_class,
            theme=request.theme,
            research_status=status,
            committee_summary=(
                f"Offline demonstration for {request.symbol}: thematic evidence is "
                f"{'present' if evidence_count else 'not established'}, but a live valuation and "
                "full filing review are required before deeper consideration."
            ),
            scorecard=ScoreCard(
                business_quality=60.0 if evidence_count else 30.0,
                growth_durability=58.0 if evidence_count else 25.0,
                financial_strength=55.0 if evidence_count else 25.0,
                valuation=valuation,
                thematic_exposure=exposure,
                evidence_confidence=evidence_confidence,
                risk=risk,
                portfolio_fit=max(0.0, 100.0 - float(overlap["score"])),
            ),
            first_rejection=rejection,
            bull_case="The supplied evidence may support a durable beneficiary pathway if future filings quantify exposure and economics.",
            base_case="The theme develops, but competition and valuation limit excess returns relative to a diversified benchmark.",
            bear_case="The narrative is real but exposure is overstated, expectations are already priced in, or capital intensity erodes returns.",
            what_would_make_it_investable=[
                "Current valuation and peer-comparison dataset",
                "Primary-source proof of revenue, backlog, or customer exposure",
                "Portfolio look-through confirming acceptable concentration",
            ],
            what_would_invalidate=[
                "Multi-quarter deterioration in the identified theme-linked business",
                "Loss of competitive position or adverse regulatory change",
                "Evidence that the claimed exposure is primarily promotional rather than economic",
            ],
            next_research_steps=[
                "Ingest the latest 10-K, 10-Q, 8-K, and earnings materials",
                "Calculate historical and peer valuation ranges deterministically",
                "Run ETF and single-name portfolio overlap analysis",
            ],
            evidence_ids=ids,
            unresolved_questions=[
                "How much current revenue and free cash flow are attributable to the theme?",
                "What growth expectations are embedded in the current market price?",
            ],
            as_of=date.today(),
        )
