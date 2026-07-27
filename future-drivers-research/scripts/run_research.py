#!/usr/bin/env python3
"""Run one research request against the Investment Committee.

    python scripts/run_research.py --symbol NVDA
    python scripts/run_research.py --theme "grid modernization"
    python scripts/run_research.py --changes NVDA
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fdr import runner  # noqa: E402

SYMBOL_PROMPT = """Research {symbol} end to end.

Prove whether its exposure to its claimed themes is real, test what
expectations the current price embeds, construct the bear case, and produce
the final research card with a computed research status.

If theme exposure cannot be proven from filings, stop there and say what
disclosure would change the answer."""

THEME_PROMPT = """Investigate the theme: {theme}.

Establish why it matters now with datable evidence, map the companies and funds
with potential exposure, then take the two most promising candidates through
evidence and risk review. Produce a research card for each.

Include at least one candidate that would complicate or falsify the theme."""

CHANGES_PROMPT = """Review {symbol} for material change since the last review.

Load the stored dossier, run change detection, and report what moved. Lead with
any invalidation condition that now appears to have been met. If nothing
material changed, say so plainly rather than manufacturing an update."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbol", help="Research a single ticker end to end.")
    group.add_argument("--theme", help="Investigate a theme and its candidates.")
    group.add_argument("--changes", metavar="SYMBOL", help="Report change since last review.")
    group.add_argument("--prompt", help="Send an arbitrary request.")
    parser.add_argument("--quiet", action="store_true", help="Suppress streaming output.")
    args = parser.parse_args()

    if args.symbol:
        prompt = SYMBOL_PROMPT.format(symbol=args.symbol.upper())
        title = f"Research {args.symbol.upper()}"
    elif args.theme:
        prompt = THEME_PROMPT.format(theme=args.theme)
        title = f"Theme: {args.theme}"
    elif args.changes:
        prompt = CHANGES_PROMPT.format(symbol=args.changes.upper())
        title = f"Change review {args.changes.upper()}"
    else:
        prompt = args.prompt
        title = "Ad hoc research"

    result = runner.run_session(prompt, title=title, verbose=not args.quiet)

    print(f"\n\n--- status: {result.status} ---")
    print(f"tool calls: {len(result.tool_calls)}")
    if result.outputs:
        print("outputs:")
        for output in result.outputs:
            print(f"  {output.get('filename')}  ({output.get('size')} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
