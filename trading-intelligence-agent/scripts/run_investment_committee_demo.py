"""Run the four-agent investment committee in live or deterministic demo mode."""
from __future__ import annotations

import argparse
import asyncio
import json

from dotenv import load_dotenv

from packages.investment_agents.models import EvidenceItem, ResearchRequest
from packages.investment_agents.orchestrator import InvestmentResearchOrchestrator


def build_demo_request(symbol: str, theme: str) -> ResearchRequest:
    """Return a small, explicitly synthetic evidence bundle for installation testing."""
    return ResearchRequest(
        symbol=symbol,
        asset_name=f"{symbol} demonstration candidate",
        asset_class="stock",
        theme=theme,
        horizon_years=7,
        existing_positions=["VOO", "QQQM", "SMH"],
        question="Does this candidate deserve deeper long-term research based on supplied evidence?",
        evidence=[
            EvidenceItem(
                evidence_id="DEMO-FILING-1",
                source_name="Synthetic annual filing fixture",
                source_type="primary_fixture",
                source_url=None,
                published_at="2026-01-15",
                summary="Management reports growing demand related to the selected theme, but the fixture does not quantify valuation.",
                reliability=0.90,
                freshness_days=30,
            ),
            EvidenceItem(
                evidence_id="DEMO-EARNINGS-1",
                source_name="Synthetic earnings fixture",
                source_type="primary_fixture",
                source_url=None,
                published_at="2026-04-20",
                summary="Backlog and customer interest increased, while capital intensity and competitive pressure remain material risks.",
                reliability=0.85,
                freshness_days=12,
            ),
        ],
    )


async def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run the four-agent investment committee demo.")
    parser.add_argument("--symbol", default="DEMO")
    parser.add_argument("--theme", default="industrial robotics and AI infrastructure")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call the OpenAI Agents SDK. Requires OPENAI_API_KEY and DEMO_MODE=false.",
    )
    args = parser.parse_args()

    request = build_demo_request(args.symbol.upper(), args.theme)
    orchestrator = InvestmentResearchOrchestrator()
    dossier = await orchestrator.run(request) if args.live else await orchestrator.run_offline_demo(request)
    print(json.dumps(dossier.model_dump(mode="json"), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
