"""Runtime settings.

Every credential is read here and stays in the orchestrator process. Nothing in
this module is ever passed into an agent session — the sandbox reaches external
data only by asking us to make the call on its behalf (see ``fdr.tools``).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Offline mode: tools serve fixtures instead of calling the network, so the
    # whole pipeline is exercisable with no keys and no rate limits.
    demo_mode: bool = field(default_factory=lambda: _flag("FDR_DEMO_MODE", True))

    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("FDR_MODEL", "claude-opus-5"))

    # Populated by scripts/provision_agents.sh; sessions reference these.
    environment_id: str = field(default_factory=lambda: os.getenv("FDR_ENVIRONMENT_ID", ""))
    committee_agent_id: str = field(default_factory=lambda: os.getenv("FDR_COMMITTEE_AGENT_ID", ""))

    # SEC requires a descriptive UA with contact details on every request.
    edgar_user_agent: str = field(
        default_factory=lambda: os.getenv(
            "EDGAR_USER_AGENT", "future-drivers-research/0.1 (contact@example.com)"
        )
    )
    fred_api_key: str = field(default_factory=lambda: os.getenv("FRED_API_KEY", ""))
    market_api_key: str = field(default_factory=lambda: os.getenv("FDR_MARKET_API_KEY", ""))

    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("FDR_DATA_DIR", str(PROJECT_ROOT / "data")))
    )
    config_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "config")

    http_timeout_seconds: float = 20.0

    def require_live_credentials(self) -> None:
        """Fail loudly rather than silently degrading to fixtures."""
        if self.demo_mode:
            return
        if not self.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is unset and FDR_DEMO_MODE is false. "
                "Set the key, or run in demo mode."
            )


_settings: Settings | None = None


def get_settings(refresh: bool = False) -> Settings:
    global _settings
    if _settings is None or refresh:
        _settings = Settings()
    return _settings
