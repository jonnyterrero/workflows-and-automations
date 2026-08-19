"""Four-agent investment research workflow built on the OpenAI Agents SDK."""

from packages.investment_agents.models import InvestmentCommitteeDossier, ResearchRequest
from packages.investment_agents.orchestrator import InvestmentResearchOrchestrator

__all__ = ["InvestmentCommitteeDossier", "InvestmentResearchOrchestrator", "ResearchRequest"]
