"""Provider-agnostic LLM adapter for OpenAI and Anthropic."""
from __future__ import annotations

import json
import os
from typing import Any

import structlog

logger = structlog.get_logger()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

DISCLAIMER = (
    "DISCLAIMER: This output is research and decision-support material generated "
    "by an AI system. It is NOT financial advice. Every claim is based on stored "
    "data evidence cited by ID. Past performance does not predict future results. "
    "Always consult a qualified financial advisor before making investment decisions."
)


class LLMAdapter:
    """Provider-agnostic LLM wrapper. Falls back to template responses in demo mode."""

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> str:
        if DEMO_MODE or (not OPENAI_API_KEY and not ANTHROPIC_API_KEY):
            return self._demo_response(user_prompt)

        if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            return await self._anthropic_complete(system_prompt, user_prompt, max_tokens, temperature)
        if OPENAI_API_KEY:
            return await self._openai_complete(system_prompt, user_prompt, max_tokens, temperature)
        return self._demo_response(user_prompt)

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_hint: str = "",
        max_tokens: int = 3000,
    ) -> dict[str, Any]:
        """Request structured JSON output. Falls back to empty dict in demo mode."""
        full_system = (
            system_prompt
            + "\n\nYou MUST respond with valid JSON only. No markdown fences, no prose."
            + (f"\n\nExpected JSON structure:\n{schema_hint}" if schema_hint else "")
            + "\n\nCritical: Only cite evidence IDs that exist in the context you were given. Never invent sources."
        )
        raw = await self.complete(full_system, user_prompt, max_tokens=max_tokens, temperature=0.2)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("llm_json_parse_failed", raw_len=len(raw))
            return {}

    async def _openai_complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float,
    ) -> str:
        try:
            from openai import AsyncOpenAI  # type: ignore
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("openai_request_failed", error=str(exc))
            return self._demo_response(user_prompt)

    async def _anthropic_complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float,
    ) -> str:
        try:
            import anthropic  # type: ignore
            client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            message = await client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text if message.content else ""
        except Exception as exc:
            logger.error("anthropic_request_failed", error=str(exc))
            return self._demo_response(user_prompt)

    def _demo_response(self, prompt: str) -> str:
        return (
            f"[DEMO MODE — No LLM API key configured]\n\n"
            f"This is a placeholder response for: {prompt[:100]}...\n\n"
            f"To enable real AI analysis, set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file "
            f"and set DEMO_MODE=false.\n\n{DISCLAIMER}"
        )
