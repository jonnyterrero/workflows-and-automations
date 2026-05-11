"""Tools for the Second Brain agent.

Backed by a local JSON store by default so the starter is self-contained;
flip USE_NOTION=true (and set NOTION_* env vars) to read/write your real Notion DBs.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from agents import function_tool

from ..common.config import settings
from ..common.logging import get_logger

log = get_logger(__name__)
USE_NOTION = bool(settings.notion_api_key)
STORE = Path(os.getenv("LOCAL_STORE_DIR", "/tmp/agent_trio_store"))
STORE.mkdir(parents=True, exist_ok=True)


def _load(name: str) -> list[dict[str, Any]]:
    p = STORE / f"{name}.json"
    if not p.exists():
        return []
    return json.loads(p.read_text() or "[]")


def _save(name: str, data: list[dict[str, Any]]) -> None:
    (STORE / f"{name}.json").write_text(json.dumps(data, indent=2, default=str))


def _notion_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


@function_tool
def add_task(title: str, due: str | None = None, priority: str = "medium", notes: str = "") -> dict[str, Any]:
    """Create a task. Priority: low | medium | high. Due ISO date YYYY-MM-DD."""
    task = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "due": due,
        "priority": priority,
        "notes": notes,
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
    }
    if USE_NOTION and settings.notion_tasks_db:
        try:
            payload = {
                "parent": {"database_id": settings.notion_tasks_db},
                "properties": {
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Priority": {"select": {"name": priority}},
                    **({"Due": {"date": {"start": due}}} if due else {}),
                },
                "children": (
                    [{"object": "block", "type": "paragraph",
                      "paragraph": {"rich_text": [{"type": "text", "text": {"content": notes}}]}}]
                    if notes else []
                ),
            }
            r = httpx.post("https://api.notion.com/v1/pages", json=payload, headers=_notion_headers(), timeout=20)
            r.raise_for_status()
            task["notion_id"] = r.json().get("id")
        except Exception as e:  # noqa: BLE001
            log.warning("notion task create failed: %s", e)

    tasks = _load("tasks")
    tasks.append(task)
    _save("tasks", tasks)
    return task


@function_tool
def list_tasks(status: str = "open") -> list[dict[str, Any]]:
    """List tasks filtered by status: open | done | all."""
    tasks = _load("tasks")
    if status == "all":
        return tasks
    return [t for t in tasks if t.get("status") == status]


@function_tool
def complete_task(task_id: str) -> dict[str, Any]:
    """Mark a task as completed by its short id."""
    tasks = _load("tasks")
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            t["completed_at"] = datetime.utcnow().isoformat()
            _save("tasks", tasks)
            return t
    return {"error": f"task {task_id} not found"}


@function_tool
def add_note(title: str, body: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Save a note to your second brain."""
    note = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "body": body,
        "tags": tags or [],
        "created_at": datetime.utcnow().isoformat(),
    }
    notes = _load("notes")
    notes.append(note)
    _save("notes", notes)
    return note


@function_tool
def search_notes(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """Substring search across saved notes."""
    q = query.lower()
    notes = _load("notes")
    hits = [n for n in notes if q in n["title"].lower() or q in n["body"].lower() or q in " ".join(n.get("tags", [])).lower()]
    return hits[:limit]


@function_tool
def daily_brief() -> dict[str, Any]:
    """Compile today's open tasks + recent notes into a single brief."""
    tasks = [t for t in _load("tasks") if t.get("status") == "open"]
    tasks.sort(key=lambda t: (t.get("due") or "9999", {"high": 0, "medium": 1, "low": 2}.get(t.get("priority", "medium"), 1)))
    notes = sorted(_load("notes"), key=lambda n: n["created_at"], reverse=True)[:5]
    return {"date": datetime.utcnow().date().isoformat(), "open_tasks": tasks, "recent_notes": notes}
