"""CLI runner. Usage:

    python -m agent_trio.runner                     # interactive REPL with Atlas
    python -m agent_trio.runner --agent trading     # talk to TradeDesk directly
    python -m agent_trio.runner --agent research -p "summarize attention is all you need"
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from rich.console import Console
from rich.markdown import Markdown

from .agents.second_brain_agent import build_second_brain_agent
from .agents.trading_agent import build_trading_agent
from .agents.research_agent import build_research_agent
from .common.logging import get_logger

console = Console()
log = get_logger(__name__)

AGENTS = {
    "atlas": build_second_brain_agent,   # default - routes via handoffs
    "trading": build_trading_agent,
    "research": build_research_agent,
}


async def run_once(agent_key: str, prompt: str, session_id: str | None = None) -> str:
    agent = AGENTS[agent_key]()
    session = SQLiteSession(session_id) if session_id else None
    try:
        result = await Runner.run(agent, prompt, session=session)
        return result.final_output
    except InputGuardrailTripwireTriggered as e:
        return f"[guardrail blocked input] {e}"
    except OutputGuardrailTripwireTriggered as e:
        return f"[guardrail blocked output] {e}"


async def repl(agent_key: str) -> None:
    agent = AGENTS[agent_key]()
    session = SQLiteSession(f"cli-{agent_key}")
    console.print(f"[bold cyan]Connected to {agent.name}.[/]  Ctrl-C to exit.\n")
    while True:
        try:
            prompt = console.input("[bold green]you ›[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye.")
            return
        if not prompt:
            continue
        try:
            result = await Runner.run(agent, prompt, session=session)
            console.print(f"\n[bold magenta]{result.last_agent.name} ›[/]")
            console.print(Markdown(str(result.final_output)))
            console.print()
        except InputGuardrailTripwireTriggered as e:
            console.print(f"[yellow]input guardrail blocked:[/] {e}\n")
        except OutputGuardrailTripwireTriggered as e:
            console.print(f"[yellow]output guardrail blocked:[/] {e}\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--agent", choices=AGENTS.keys(), default="atlas")
    p.add_argument("-p", "--prompt", help="Single-shot prompt; omit to enter REPL.")
    p.add_argument("--session", help="Session id for persistent memory across runs.")
    args = p.parse_args()

    if args.prompt:
        out = asyncio.run(run_once(args.agent, args.prompt, args.session))
        console.print(Markdown(str(out)))
    else:
        asyncio.run(repl(args.agent))


if __name__ == "__main__":
    main()
