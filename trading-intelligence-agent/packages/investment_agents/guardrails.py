"""Input and output guardrails for the investment research workflow."""
from __future__ import annotations

import re

from agents import GuardrailFunctionOutput, RunContextWrapper, TResponseInputItem, input_guardrail, output_guardrail

from packages.investment_agents.models import InvestmentCommitteeDossier, ResearchRequest

_DIRECTIVE_PATTERNS = (
    r"\bbuy now\b",
    r"\bsell now\b",
    r"\bguaranteed return\b",
    r"\bwill definitely (rise|fall|go up|go down)\b",
)


@input_guardrail
async def research_request_guardrail(
    ctx: RunContextWrapper[None], agent: object, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """Reject requests framed as guaranteed-return or immediate trade instructions."""
    text = input if isinstance(input, str) else str(input)
    blocked = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in _DIRECTIVE_PATTERNS)
    return GuardrailFunctionOutput(
        output_info={"reason": "Direct trading or guaranteed-return language is not allowed."} if blocked else {},
        tripwire_triggered=blocked,
    )


@output_guardrail
async def dossier_output_guardrail(
    ctx: RunContextWrapper[None], agent: object, output: InvestmentCommitteeDossier
) -> GuardrailFunctionOutput:
    """Ensure final dossiers remain evidence-linked and decision-support framed."""
    joined = " ".join(
        [output.committee_summary, output.bull_case, output.base_case, output.bear_case]
    )
    unsafe_language = any(re.search(pattern, joined, flags=re.IGNORECASE) for pattern in _DIRECTIVE_PATTERNS)
    missing_review_language = "human review" not in output.disclaimer.lower()
    triggered = unsafe_language or missing_review_language
    return GuardrailFunctionOutput(
        output_info={
            "unsafe_language": unsafe_language,
            "missing_human_review_language": missing_review_language,
        },
        tripwire_triggered=triggered,
    )


def validate_request(request: ResearchRequest) -> ResearchRequest:
    """Provide an explicit non-agent validation entrypoint for API callers and tests."""
    if not request.question.strip():
        raise ValueError("Research question cannot be empty")
    return request
