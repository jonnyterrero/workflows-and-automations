"""Drive a Managed Agents research session.

Three client behaviours here are load-bearing and easy to get subtly wrong:

* **Stream first.** The event stream only delivers what happens after it opens.
  We create the session with no initial events, open the stream, and only then
  send the kickoff — otherwise the opening exchange arrives as one buffered
  lump and custom tool calls in it can be missed.
* **Idle is not done.** A session goes idle whenever it needs something from
  us, including every custom tool call. Breaking on the first idle would
  abandon the run mid-research. We continue while ``stop_reason`` is
  ``requires_action`` and stop only on a terminal reason.
* **Echo the thread id, and answer one call per request.** In a multiagent
  session a subagent's tool call is cross-posted to the primary thread carrying
  ``session_thread_id``; the reply must carry it back. Replies also cannot be
  batched: each is resolved against the call it names, and once subagents run
  concurrently a batch inevitably spans turns, so the later ids are no longer
  pending and the whole request is rejected.
* **Reconcile the backlog on every reconnect.** The stream has no replay, so a
  call emitted between two connections is invisible to the live feed and the
  session waits on it forever. Each iteration re-derives outstanding calls from
  ``events.list`` before reading the stream.

All four were found by running real sessions, not by reading the docs.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from fdr.config import get_settings
from fdr.tools import registry

# Guard against a pathological loop if a session keeps requesting action we
# cannot satisfy. Generous, because legitimate multi-agent research is chatty.
MAX_TURNS = 60

# How many times to re-reconcile when the session reports it is blocked but we
# can see nothing to answer.
REQUIRES_ACTION_RETRIES = 3


@dataclass
class SessionResult:
    session_id: str
    transcript: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    status: str = "unknown"
    console_url: str = ""

    @property
    def text(self) -> str:
        return "\n".join(self.transcript)


def _client() -> Any:
    settings = get_settings()
    import anthropic  # imported lazily so offline tests need no SDK credentials

    if settings.anthropic_api_key:
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    # Falls back to an `ant auth login` profile if one is active.
    return anthropic.Anthropic()


def _block_text(block: Any) -> str:
    if getattr(block, "type", None) == "text":
        return getattr(block, "text", "") or ""
    return ""


def _tool_payload(event: Any) -> dict[str, Any]:
    raw = getattr(event, "input", None)
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def _result_event(event: Any, result: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "user.custom_tool_result",
        "custom_tool_use_id": event.id,
        "content": [{"type": "text", "text": json.dumps(result, default=str)}],
    }
    # Present only in multiagent sessions; routes the result back to the
    # subagent thread that asked for it.
    thread_id = getattr(event, "session_thread_id", None)
    if thread_id:
        payload["session_thread_id"] = thread_id
    return payload


def _pending_tool_calls(
    client: Any, session_id: str, attempted: set[str]
) -> list[Any]:
    """Tool calls the session is still waiting on, from server state.

    The stream has no replay, so a call emitted between two connections is
    invisible to the live feed — the session simply sits idle with
    ``requires_action`` forever. Reconciling against ``events.list`` on every
    reconnect is what closes that gap.

    Derived from the server's own record of which calls have results, rather
    than from what this process remembers sending.
    """
    try:
        events = list(client.beta.sessions.events.list(session_id=session_id))
    except Exception:  # noqa: BLE001 - backlog reconciliation is best-effort
        return []

    answered_ids = {
        getattr(e, "custom_tool_use_id", None)
        for e in events
        if "custom_tool_result" in getattr(e, "type", "")
    }
    return [
        e
        for e in events
        if getattr(e, "type", "") == "agent.custom_tool_use"
        and e.id not in answered_ids
        and e.id not in attempted
    ]


def _answer_tool_call(
    client: Any,
    session_id: str,
    event: Any,
    result: SessionResult,
    verbose: bool,
    attempted: set[str] | None = None,
) -> bool:
    """Execute one custom tool call and return its result to the right thread.

    Sent as its own request. Each reply is resolved against the pending call it
    names, so one request per call is the granularity that always holds —
    batching only works when every id in the batch is still pending, which is
    not guaranteed once subagents run concurrently.

    A rejected reply is logged rather than raised: a single stale id should not
    abandon a session that has already done real research.
    """
    name = getattr(event, "name", "")
    payload = _tool_payload(event)
    if attempted is not None:
        attempted.add(getattr(event, "id", ""))
    tool_result = registry.dispatch(name, payload)
    result.tool_calls.append({"tool": name, "input": payload})

    try:
        client.beta.sessions.events.send(
            session_id=session_id, events=[_result_event(event, tool_result)]
        )
    except Exception as exc:  # noqa: BLE001 - reported, session continues
        result.transcript.append(f"[tool reply rejected] {name}: {exc}")
        if verbose:
            print(f"\n[! {name} reply rejected]", flush=True)
        return False

    if verbose:
        marker = "!" if "error" in tool_result else "+"
        print(f"\n[{marker} {name}]", flush=True)
    return True


def create_session(
    client: Any,
    agent_id: str,
    environment_id: str,
    title: str,
) -> Any:
    """Create a session with no initial events, so we can stream first."""
    return client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title=title,
    )


def run_session(
    prompt: str,
    agent_id: str | None = None,
    environment_id: str | None = None,
    title: str = "Research run",
    verbose: bool = True,
) -> SessionResult:
    """Run one research request to completion and return the transcript."""
    settings = get_settings()
    agent_id = agent_id or settings.committee_agent_id
    environment_id = environment_id or settings.environment_id

    if not agent_id or not environment_id:
        raise RuntimeError(
            "FDR_COMMITTEE_AGENT_ID and FDR_ENVIRONMENT_ID must be set. "
            "Run: python scripts/provision_agents.py"
        )

    client = _client()
    session = create_session(client, agent_id, environment_id, title)
    result = SessionResult(
        session_id=session.id,
        console_url=f"https://platform.claude.com/workspaces/default/sessions/{session.id}",
    )
    if verbose:
        print(f"session {session.id}\ntrace   {result.console_url}\n")

    pending_kickoff = True
    attempted: set[str] = set()
    idle_without_work = 0

    for _ in range(MAX_TURNS):
        answered = 0
        terminated = False
        stop_reason = ""

        with client.beta.sessions.events.stream(session_id=session.id) as stream:
            # Stream is open and buffering; now it is safe to send.
            if pending_kickoff:
                client.beta.sessions.events.send(
                    session_id=session.id,
                    events=[
                        {"type": "user.message", "content": [{"type": "text", "text": prompt}]}
                    ],
                )
                pending_kickoff = False

            # Reconcile against server state before reading the live feed, so
            # calls emitted while we were disconnected are not stranded.
            for call in _pending_tool_calls(client, session.id, attempted):
                if _answer_tool_call(client, session.id, call, result, verbose, attempted):
                    answered += 1

            for event in stream:
                etype = getattr(event, "type", "")

                if etype == "agent.message":
                    chunk = "".join(_block_text(b) for b in getattr(event, "content", []))
                    if chunk:
                        result.transcript.append(chunk)
                        if verbose:
                            print(chunk, end="", flush=True)

                elif etype == "agent.custom_tool_use":
                    # Answer immediately, while this call is still the pending
                    # one for its thread. Collecting calls and replying in a
                    # batch at idle looks tidier but breaks: subagents run
                    # asynchronously, so a backlog spans several turns, and by
                    # the time we reply the earlier ids are no longer pending.
                    if getattr(event, "id", None) in attempted:
                        continue
                    if _answer_tool_call(
                        client, session.id, event, result, verbose, attempted
                    ):
                        answered += 1

                elif etype == "session.thread_created":
                    if verbose:
                        name = getattr(event, "agent_name", "subagent")
                        print(f"\n[delegating to {name}]\n", flush=True)

                elif etype == "session.error":
                    message = getattr(getattr(event, "error", None), "message", "unknown")
                    result.transcript.append(f"[session error] {message}")
                    if verbose:
                        print(f"\n[session error] {message}", flush=True)

                elif etype == "session.status_idle":
                    stop_reason = getattr(getattr(event, "stop_reason", None), "type", "") or ""
                    break

                elif etype == "session.status_terminated":
                    terminated = True
                    break

        if terminated:
            result.status = "terminated"
            break

        if answered:
            idle_without_work = 0
            continue

        # Idle with no work for us. `requires_action` means the session is
        # blocked on something we have not supplied; the next iteration
        # reconciles against server state, which usually surfaces it. Retry a
        # bounded number of times before giving up, since the alternative is
        # abandoning a session that is only a beat ahead of us.
        if stop_reason == "requires_action":
            idle_without_work += 1
            if idle_without_work <= REQUIRES_ACTION_RETRIES:
                time.sleep(2.0)
                continue
            result.status = "requires_action_unhandled"
            break

        result.status = stop_reason or "idle"
        break
    else:
        result.status = "max_turns_exceeded"

    result.outputs = fetch_outputs(client, session.id)
    return result


def fetch_outputs(client: Any, session_id: str, retries: int = 3) -> list[dict[str, Any]]:
    """Files the agent wrote to /mnt/session/outputs/.

    Indexing lags session idle by a second or two, so an empty first list is
    expected rather than meaningful.
    """
    for attempt in range(retries):
        try:
            listing = client.beta.files.list(
                scope_id=session_id, betas=["managed-agents-2026-04-01"]
            )
        except Exception as exc:  # noqa: BLE001 - outputs are best-effort
            return [{"error": f"{type(exc).__name__}: {exc}"}]

        rows = [
            {"id": f.id, "filename": getattr(f, "filename", ""), "size": getattr(f, "size_bytes", 0)}
            for f in getattr(listing, "data", [])
        ]
        if rows or attempt == retries - 1:
            return rows
        time.sleep(1.5)
    return []


def download_output(client: Any, file_id: str) -> bytes:
    response = client.beta.files.download(file_id)
    if hasattr(response, "read"):
        return response.read()
    return bytes(response)
