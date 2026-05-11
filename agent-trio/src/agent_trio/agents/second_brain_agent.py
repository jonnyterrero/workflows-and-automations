"""Second-brain / secretary agent. Acts as the front-door router via handoffs."""
from __future__ import annotations

from agents import Agent, ModelSettings, handoff

from ..common.config import settings
from ..tools.notion_tools import (
    add_task,
    list_tasks,
    complete_task,
    add_note,
    search_notes,
    daily_brief,
)
from .trading_agent import build_trading_agent
from .research_agent import build_research_agent

INSTRUCTIONS = """\
You are Atlas, the user's second brain and chief of staff.

You manage three things:
1. Tasks  (add_task, list_tasks, complete_task)
2. Notes  (add_note, search_notes)
3. Daily orientation (daily_brief)

You also ROUTE work to specialists when a request is out of scope:
- Markets, tickers, trading -> hand off to TradeDesk.
- Academic research, papers, homework, technical deep dives -> hand off to Scholar.

ROUTING RULES
- If the user's message is clearly market/ticker work (e.g. mentions a ticker,
  'should I trade', earnings, charts), call transfer_to_TradeDesk.
- If the message asks for literature review, paper summaries, or homework
  explanation, call transfer_to_Scholar.
- For everything else (todos, notes, plans, scheduling thoughts, journaling,
  daily briefs) handle it yourself with the tools above.
- If a message blends both (e.g. 'add a task to research NVDA earnings'),
  CREATE the task first, THEN hand off so the specialist can do the actual work.

STYLE
- Crisp, direct, no fluff. Confirm writes with a one-line summary
  (e.g. 'Task #a1b2 added, due 2025-05-15, high priority').
- Default to bullet lists for status views.
"""


def build_second_brain_agent() -> Agent:
    trading = build_trading_agent()
    research = build_research_agent()
    return Agent(
        name="Atlas",
        handoff_description="Personal second brain: tasks, notes, daily briefs, and routing.",
        instructions=INSTRUCTIONS,
        model=settings.model,
        model_settings=ModelSettings(temperature=0.2),
        tools=[add_task, list_tasks, complete_task, add_note, search_notes, daily_brief],
        handoffs=[handoff(trading), handoff(research)],
    )
