"""Research guardrails: detect academic-integrity violations on input."""
from __future__ import annotations

from pydantic import BaseModel, Field
from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, input_guardrail

from ..common.config import settings


class IntegrityCheck(BaseModel):
    is_dishonest_request: bool = Field(description="True if user asks the agent to take a graded test, write a final exam answer, or impersonate them on an assessment.")
    reasoning: str


_screen = Agent(
    name="Academic-Integrity Screen",
    instructions=(
        "Decide if the user is asking the agent to commit academic dishonesty: "
        "writing a graded exam answer for them, completing an online proctored test, "
        "or impersonating them on an assessment. Helping them STUDY, understand "
        "material, draft an essay outline, or check their own work is fine."
    ),
    output_type=IntegrityCheck,
    model=settings.model,
)


@input_guardrail
async def block_dishonest_requests(ctx: RunContextWrapper, agent: Agent, user_input):
    text = user_input if isinstance(user_input, str) else str(user_input)
    result = await Runner.run(_screen, text, context=ctx.context)
    out: IntegrityCheck = result.final_output
    return GuardrailFunctionOutput(output_info=out.reasoning, tripwire_triggered=out.is_dishonest_request)
