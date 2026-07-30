"""Turn API failures into messages that say what to do next.

The failures a first-time setup actually hits — no credits, a rejected key, a
stale agent ID in .env — all arrive as a generic ``BadRequestError`` whose one
useful line is buried under a stack trace.
"""
from __future__ import annotations


def explain(exc: Exception) -> str:
    """Actionable description of an API failure, or the raw message."""
    message = str(exc)

    if "credit balance is too low" in message:
        return (
            "The API key is valid, but the account has no credits.\n"
            "  Add credits at https://console.anthropic.com/settings/billing, "
            "then re-run.\n"
            "  Existing resources are reused, so re-running is safe."
        )
    if "Invalid agent ID" in message:
        return (
            "The agent ID was rejected. FDR_COMMITTEE_AGENT_ID in .env is stale "
            "or belongs to another workspace.\n"
            "  Re-run: python scripts/provision_agents.py"
        )
    if "Invalid environment ID" in message or "environment_id" in message:
        return (
            "The environment ID was rejected. FDR_ENVIRONMENT_ID in .env is "
            "stale or belongs to another workspace.\n"
            "  Re-run: python scripts/provision_agents.py"
        )
    if "authentication_error" in message or "invalid x-api-key" in message:
        return (
            "The API key was rejected. Check ANTHROPIC_API_KEY in .env, "
            "or run `ant auth login`."
        )
    if "permission_error" in message:
        return "The API key lacks permission for Managed Agents on this workspace."
    if "rate_limit_error" in message:
        return "Rate limited. Wait and re-run; the SDK already retries transient limits."

    return message


def is_explained(exc: Exception) -> bool:
    """Whether ``explain`` has something better than the raw message."""
    return explain(exc) != str(exc)
