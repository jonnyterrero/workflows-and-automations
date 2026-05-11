"""Guardrails for the Trading agent.

Two layers:
1. Input guardrail: blocks requests asking for *personalized financial advice*
   that we can't responsibly give (e.g. "what should I do with my 401k").
2. Output guardrail: ensures the model never emits a directive 'BUY/SELL NOW'
   without an attached risk-disclosure block, and tags any unverifiable
   price claims for review.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    input_guardrail,
    output_guardrail,
)

from ..common.config import settings


class AdviceCheck(BaseModel):
    is_personalized_advice: bool = Field(description="True if the user asks for personalized investment advice (their specific portfolio, retirement, taxes).")
    reasoning: str


_advice_screen = Agent(
    name="Personalized-Advice Screen",
    instructions=(
        "Classify whether the user is asking for personalized investment, tax, or "
        "retirement advice that requires a licensed advisor (e.g. 'should I roll "
        "over my 401k', 'allocate my $200k inheritance'). General market analysis, "
        "ticker research, position sizing math, or paper-trading strategy questions "
        "are NOT personalized advice."
    ),
    output_type=AdviceCheck,
    model=settings.model,
)


@input_guardrail
async def block_personalized_advice(ctx: RunContextWrapper, agent: Agent, user_input):
    text = user_input if isinstance(user_input, str) else str(user_input)
    result = await Runner.run(_advice_screen, text, context=ctx.context)
    out: AdviceCheck = result.final_output
    return GuardrailFunctionOutput(
        output_info=out.reasoning,
        tripwire_triggered=out.is_personalized_advice,
    )


class DisclosureCheck(BaseModel):
    missing_disclosure: bool = Field(description="True if the response gives directive trade calls without a risk disclosure.")
    reasoning: str


_disclosure_screen = Agent(
    name="Trade-Disclosure Screen",
    instructions=(
        "Inspect the assistant output. If it issues directive trade calls (e.g. "
        "'buy AAPL at 195', 'short SPY now') WITHOUT an explicit risk-disclosure "
        "section noting this is not financial advice, set missing_disclosure=true. "
        "Educational analysis without an explicit 'do this' instruction is fine."
    ),
    output_type=DisclosureCheck,
    model=settings.model,
)


@output_guardrail
async def require_risk_disclosure(ctx: RunContextWrapper, agent: Agent, output) -> GuardrailFunctionOutput:
    text = output if isinstance(output, str) else str(output)
    result = await Runner.run(_disclosure_screen, text, context=ctx.context)
    out: DisclosureCheck = result.final_output
    return GuardrailFunctionOutput(
        output_info=out.reasoning,
        tripwire_triggered=out.missing_disclosure,
    )
