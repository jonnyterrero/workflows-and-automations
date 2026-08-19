"""Host-executed tools.

Every module here runs in the orchestrator process, never in the agent
sandbox. That is what keeps SEC, FRED, and market credentials out of reach of
sandboxed code and of anything an agent might read from an untrusted document.
"""
from __future__ import annotations

from fdr.tools import changes, filings, journal, macro, market, portfolio

__all__ = ["changes", "filings", "journal", "macro", "market", "portfolio"]
